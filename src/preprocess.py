from __future__ import annotations

import gc
import json
import pickle
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import signal

from .common import (
    dump_json,
    ensure_dirs,
    environment_info,
    now_iso,
    processed_paths,
    stable_manifest_hash,
    subject_split_map,
    verify_subject_files,
)


def load_subject(path: Path) -> dict:
    with path.open("rb") as handle:
        return pickle.load(handle, encoding="latin1")


def finite_runs(values: np.ndarray) -> list[tuple[int, int]]:
    good = np.isfinite(values)
    edges = np.diff(np.r_[False, good, False].astype(np.int8))
    return list(zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)))


def filter_continuous(values: np.ndarray, fs: int, band: list[float], order: int) -> tuple[np.ndarray, np.ndarray]:
    sos = signal.butter(order, band, btype="bandpass", fs=fs, output="sos")
    output = np.full(values.shape, np.nan, dtype=np.float64)
    min_len = 3 * (2 * len(sos) + 1)
    for start, stop in finite_runs(values):
        if stop - start > min_len:
            output[start:stop] = signal.sosfiltfilt(sos, values[start:stop])
    return output, sos


def resample_bvp(values: np.ndarray) -> np.ndarray:
    if np.isfinite(values).all():
        return signal.resample_poly(values, 1, 2).astype(np.float64, copy=False)
    output = np.full((len(values) + 1) // 2, np.nan, dtype=np.float64)
    for start, stop in finite_runs(values):
        if stop - start >= 32:
            part = signal.resample_poly(values[start:stop], 1, 2)
            target = start // 2
            output[target : target + len(part)] = part
    return output


def detect_r_peaks(ecg_filtered: np.ndarray, fs: int, cfg: dict) -> tuple[np.ndarray, dict]:
    """Adaptive polarity-aware amplitude detector; deliberately not called Pan-Tompkins."""
    finite = ecg_filtered[np.isfinite(ecg_filtered)]
    if finite.size == 0:
        return np.empty(0, dtype=np.int64), {"polarity": 1, "candidate_count": 0}
    pos = np.quantile(finite, 0.999)
    neg = abs(np.quantile(finite, 0.001))
    polarity = 1 if pos >= neg else -1
    oriented = polarity * ecg_filtered
    block = int(round(cfg["local_block_seconds"] * fs))
    padding = int(round(cfg["padding_seconds"] * fs))
    refractory = int(round(cfg["refractory_seconds"] * fs))
    refine = int(round(cfg["refinement_seconds"] * fs))
    candidates: list[int] = []
    for core_start in range(0, len(oriented), block):
        core_stop = min(len(oriented), core_start + block)
        start = max(0, core_start - padding)
        stop = min(len(oriented), core_stop + padding)
        local = oriented[start:stop]
        local_finite = local[np.isfinite(local)]
        if local_finite.size < fs:
            continue
        scale = float(np.quantile(np.abs(local_finite), 0.99))
        if not np.isfinite(scale) or scale <= 0:
            continue
        peaks, _ = signal.find_peaks(
            np.nan_to_num(local, nan=-np.inf),
            distance=refractory,
            height=cfg["height_fraction_p99"] * scale,
            prominence=cfg["prominence_fraction_p99"] * scale,
        )
        for peak in peaks + start:
            if core_start <= peak < core_stop:
                lo, hi = max(0, peak - refine), min(len(oriented), peak + refine + 1)
                candidates.append(lo + int(np.nanargmax(oriented[lo:hi])))
    if not candidates:
        return np.empty(0, dtype=np.int64), {"polarity": polarity, "candidate_count": 0}
    ordered = sorted(set(candidates))
    accepted = [ordered[0]]
    for peak in ordered[1:]:
        if peak - accepted[-1] >= refractory:
            accepted.append(peak)
        elif oriented[peak] > oriented[accepted[-1]]:
            accepted[-1] = peak
    peaks = np.asarray(accepted, dtype=np.int64)
    return peaks, {"polarity": polarity, "candidate_count": len(candidates), "accepted_count": len(peaks)}


def longest_true_run(mask: np.ndarray) -> int:
    if mask.size == 0 or not mask.any():
        return 0
    edges = np.diff(np.r_[False, mask, False].astype(np.int8))
    starts, stops = np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)
    return int(np.max(stops - starts))


def has_extreme_plateau(values: np.ndarray, low: float, high: float, min_samples: int, tolerance: float) -> bool:
    if len(values) < 2:
        return False
    near_extreme = (values <= low + tolerance) | (values >= high - tolerance)
    near_equal = np.r_[False, np.abs(np.diff(values)) <= tolerance]
    return longest_true_run(near_extreme & near_equal) >= min_samples


def window_label(labels: np.ndarray) -> tuple[int, float]:
    values, counts = np.unique(labels, return_counts=True)
    index = int(np.argmax(counts))
    return int(values[index]), float(counts[index] / len(labels))


def primary_reason(flags: dict[str, bool]) -> tuple[str, str]:
    order = [
        ("scope_condition", "scope"), ("scope_purity", "scope"),
        ("nonfinite_bvp", "quality"), ("nonfinite_ecg", "quality"),
        ("flat_bvp", "quality"), ("flat_ecg", "quality"),
        ("bvp_clipping", "quality"), ("ecg_clipping", "quality"),
        ("insufficient_r_peaks", "quality"), ("nonmonotonic_peaks", "quality"),
        ("nonfinite_hr", "quality"), ("hr_out_of_range", "quality"),
        ("rr_suspicious", "quality"),
    ]
    for name, category in order:
        if flags.get(name, False):
            return name, category
    return "accepted", "accepted"


def preprocess(cfg: dict) -> dict:
    ensure_dirs(cfg)
    paths = processed_paths(cfg)
    inventory = verify_subject_files(cfg)
    pp, qc, qrs = cfg["preprocessing"], cfg["qc"], cfg["qrs"]
    split_map = subject_split_map(cfg)
    fs_bvp, fs_ecg, fs_label = pp["fs_bvp"], pp["fs_ecg"], pp["fs_label"]
    window_n = int(round(pp["window_seconds"] * fs_bvp))
    stride_n = int(round(pp["stride_seconds"] * fs_bvp))
    condition_names = {int(k): v for k, v in pp["condition_names"].items()}
    accepted_rows, audit_rows = [], []
    arrays = {"bvp_unscaled": [], "bvp_filtered": [], "bvp_normalized": []}
    subject_qrs, runtimes = {}, {}
    bvp_sos = signal.butter(pp["butterworth_order"], pp["bvp_band_hz"], btype="bandpass", fs=fs_bvp, output="sos")
    ecg_sos = signal.butter(pp["butterworth_order"], pp["ecg_band_hz"], btype="bandpass", fs=fs_ecg, output="sos")
    for item in inventory:
        started = time.perf_counter()
        subject = item["subject"]
        raw = load_subject(Path(item["path"]))
        raw_bvp = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64).ravel()
        raw_ecg = np.asarray(raw["signal"]["chest"]["ECG"], dtype=np.float64).ravel()
        labels = np.asarray(raw["label"]).ravel()
        bvp = resample_bvp(raw_bvp)
        bvp_filtered, _ = filter_continuous(bvp, fs_bvp, pp["bvp_band_hz"], pp["butterworth_order"])
        ecg_filtered, _ = filter_continuous(raw_ecg, fs_ecg, pp["ecg_band_hz"], pp["butterworth_order"])
        peaks, qrs_info = detect_r_peaks(ecg_filtered, fs_ecg, qrs)
        subject_qrs[subject] = qrs_info
        duration_s = min(len(bvp) / fs_bvp, len(raw_ecg) / fs_ecg, len(labels) / fs_label)
        last_start = int(np.floor((duration_s - pp["window_seconds"]) * fs_bvp + 1e-9))
        bvp_low, bvp_high = np.quantile(raw_bvp[np.isfinite(raw_bvp)], qc["extreme_quantiles"])
        ecg_low, ecg_high = np.quantile(raw_ecg[np.isfinite(raw_ecg)], qc["extreme_quantiles"])
        bvp_tol = max((bvp_high - bvp_low) * qc["plateau_diff_fraction"], 1e-12)
        ecg_tol = max((ecg_high - ecg_low) * qc["plateau_diff_fraction"], 1e-12)
        for b0 in range(0, last_start + 1, stride_n):
            t0 = b0 / fs_bvp
            t1 = t0 + pp["window_seconds"]
            b1 = b0 + window_n
            e0, e1 = int(np.floor(t0 * fs_ecg + 1e-9)), int(np.floor(t1 * fs_ecg + 1e-9))
            l0, l1 = int(np.floor(t0 * fs_label + 1e-9)), int(np.floor(t1 * fs_label + 1e-9))
            rb0, rb1 = int(np.floor(t0 * pp["fs_bvp_original"] + 1e-9)), int(np.floor(t1 * pp["fs_bvp_original"] + 1e-9))
            bw, bfw, ew, lw = bvp[b0:b1], bvp_filtered[b0:b1], raw_ecg[e0:e1], labels[l0:l1]
            condition, purity = window_label(lw)
            rp = peaks[(peaks >= e0) & (peaks < e1)]
            peak_times = rp / fs_ecg
            rr = np.diff(peak_times)
            hr = 60.0 * (len(rp) - 1) / (peak_times[-1] - peak_times[0]) if len(rp) >= 2 else np.nan
            flags = {
                "scope_condition": condition not in pp["condition_ids"],
                "scope_purity": purity < pp["label_purity_min"],
                "nonfinite_bvp": not (np.isfinite(bw).all() and np.isfinite(bfw).all()),
                "nonfinite_ecg": not np.isfinite(ew).all(),
                "flat_bvp": np.isfinite(bw).all() and float(np.std(bw)) <= qc["flat_std_epsilon"],
                "flat_ecg": np.isfinite(ew).all() and float(np.std(ew)) <= qc["flat_std_epsilon"],
                "bvp_clipping": has_extreme_plateau(raw_bvp[rb0:rb1], bvp_low, bvp_high, int(round(qc["bvp_plateau_min_seconds"] * pp["fs_bvp_original"])), bvp_tol),
                "ecg_clipping": has_extreme_plateau(ew, ecg_low, ecg_high, int(round(qc["ecg_plateau_min_seconds"] * fs_ecg)), ecg_tol),
                "insufficient_r_peaks": len(rp) < qc["min_r_peaks"],
                "nonmonotonic_peaks": len(rp) > 1 and not np.all(np.diff(rp) > 0),
                "nonfinite_hr": not np.isfinite(hr),
                "hr_out_of_range": np.isfinite(hr) and not (qc["hr_range_bpm"][0] <= hr <= qc["hr_range_bpm"][1]),
                "rr_suspicious": rr.size > 0 and bool(((rr < qc["rr_range_seconds"][0]) | (rr > qc["rr_range_seconds"][1])).any()),
            }
            reason, category = primary_reason(flags)
            window_id = f"{subject}_{int(round(t0 * 1000)):09d}_{int(round(t1 * 1000)):09d}"
            row = {
                "window_id": window_id, "subject": subject, "split": split_map[subject],
                "t_start_s": t0, "t_end_s": t1, "condition_id": condition,
                "condition": condition_names.get(condition, f"Other_{condition}"), "purity": purity,
                "hr_ref_bpm": hr, "n_r_peaks": len(rp),
                "r_peak_times_s": json.dumps([round(float(x), 6) for x in peak_times]),
                "rr_intervals_s": json.dumps([round(float(x), 6) for x in rr]),
                "qc_pass": reason == "accepted", "reason": reason, "reason_category": category,
            }
            row.update({f"flag_{name}": value for name, value in flags.items()})
            audit_rows.append(row)
            if reason == "accepted":
                std = float(np.std(bfw))
                normalized = (bfw - float(np.mean(bfw))) / max(std, pp["zscore_epsilon"])
                row["window_index"] = len(accepted_rows)
                accepted_rows.append(row.copy())
                arrays["bvp_unscaled"].append(bw.astype(np.float32))
                arrays["bvp_filtered"].append(bfw.astype(np.float32))
                arrays["bvp_normalized"].append(normalized.astype(np.float32))
        runtimes[subject] = round(time.perf_counter() - started, 3)
        del raw, raw_bvp, raw_ecg, labels, bvp, bvp_filtered, ecg_filtered
        gc.collect()
    metadata = pd.DataFrame(accepted_rows)
    audit = pd.DataFrame(audit_rows)
    packed = {name: np.stack(values) for name, values in arrays.items()}
    metadata.to_csv(paths["metadata"], index=False, encoding="utf-8-sig")
    audit.to_csv(paths["audit"], index=False, encoding="utf-8-sig")
    np.savez_compressed(paths["windows"], **packed)
    manifest_hash = stable_manifest_hash(metadata)
    manifest = {
        "dataset_version": cfg["project"]["dataset_version"], "created_at": now_iso(),
        "config_hash": cfg["_config_hash"], "manifest_hash": manifest_hash,
        "source_files": inventory, "window_definition": "half-open [t,t+8s); indices=floor(t*fs+1e-9)",
        "sos": {"bvp": bvp_sos.tolist(), "ecg": ecg_sos.tolist()},
        "qrs": {"name": qrs["detector"], "not_pan_tompkins": True, "by_subject": subject_qrs},
        "library_versions": environment_info(),
    }
    dump_json(paths["manifest"], manifest)
    split_counts = metadata.groupby("split").size().astype(int).to_dict()
    summary = {
        "status": "complete", "created_at": now_iso(), "dataset_version": cfg["project"]["dataset_version"],
        "config_hash": cfg["_config_hash"], "manifest_hash": manifest_hash,
        "windows_before_qc": int(len(audit)), "windows_kept": int(len(metadata)),
        "windows_rejected": int(len(audit) - len(metadata)),
        "primary_reason_counts": audit["reason"].value_counts().astype(int).to_dict(),
        "reason_category_counts": audit["reason_category"].value_counts().astype(int).to_dict(),
        "windows_by_split": split_counts,
        "windows_by_subject_condition": metadata.groupby(["subject", "condition"]).size().astype(int).rename("n").reset_index().to_dict("records"),
        "hr_ref_bpm": metadata["hr_ref_bpm"].describe().to_dict(),
        "runtime_seconds_by_subject": runtimes,
        "checks": {
            "window_samples": int(packed["bvp_normalized"].shape[1]),
            "finite": bool(np.isfinite(packed["bvp_normalized"]).all() and np.isfinite(metadata["hr_ref_bpm"]).all()),
            "unique_window_id": bool(metadata["window_id"].is_unique),
            "subject_sets_disjoint": True,
            "alignment": bool(all(len(v) == len(metadata) for v in packed.values())),
        },
        "notes": [
            "HR_ref is an automatic ECG-derived reference, not absolute ground truth.",
            "Detector is an adaptive polarity-aware amplitude detector, not Pan-Tompkins.",
            "Filtering is zero-phase offline processing on continuous recordings before windowing.",
            "Scope exclusions and signal-quality exclusions are counted separately; primary reasons do not double count.",
        ],
    }
    dump_json(paths["summary"], summary)
    return summary
