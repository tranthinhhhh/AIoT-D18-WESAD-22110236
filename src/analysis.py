from __future__ import annotations

import gc
import json
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

from .common import dump_json, load_processed, now_iso
from .metrics import sample_mean_std
from .preprocess import detect_r_peaks, filter_continuous, load_subject


COLORS = {"E0": "#8c8c8c", "E1": "#4e79a7", "A0": "#e15759", "A3": "#59a14f", "A1": "#f28e2b", "A2": "#b07aa1"}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def build_result_tables(cfg: dict) -> dict:
    out = Path(cfg["project"]["output_dir"])
    baseline = _read_json(out / "baselines" / "baseline_metrics.json")
    rows = []
    for method in ("E0", "E1"):
        metric = baseline["methods"][f"{method}_test"]
        rows.append({
            "method": method, "seeds": 0, "mae_macro_mean_bpm": metric["mae_macro_bpm"],
            "mae_macro_std_bpm": np.nan, "pooled_mae_mean_bpm": metric["pooled"]["mae_bpm"],
            "pooled_rmse_mean_bpm": metric["pooled"]["rmse_bpm"], "pearson_mean": metric["pooled"]["pearson_r"],
        })
    summaries = {}
    for variant in ("A0", "A1", "A2", "A3"):
        path = out / "runs" / f"{variant}_summary.json"
        if not path.is_file():
            continue
        item = _read_json(path)
        summaries[variant] = item
        aggregate = item["aggregate_across_seeds"]
        rows.append({
            "method": variant, "seeds": len(item["seeds"]),
            "mae_macro_mean_bpm": aggregate["mae_macro_bpm"]["mean"],
            "mae_macro_std_bpm": aggregate["mae_macro_bpm"]["std_sample"],
            "pooled_mae_mean_bpm": aggregate["pooled_mae_bpm"]["mean"],
            "pooled_rmse_mean_bpm": aggregate["pooled_rmse_bpm"]["mean"],
            "pearson_mean": aggregate["pooled_pearson_r"]["mean"],
        })
    table = pd.DataFrame(rows)
    table.to_csv(out / "tables" / "overall_results_v2.csv", index=False, encoding="utf-8-sig")
    e1_subject = {x["subject"]: x["mae_bpm"] for x in baseline["methods"]["E1_test"]["by_subject"]}
    paired = []
    for seed in cfg["training"]["seeds"]:
        path = out / "runs" / f"A0_seed{seed}" / "metrics.json"
        item = _read_json(path)
        for subject_row in item["metrics"]["test"]["by_subject"]:
            subject = subject_row["subject"]
            paired.append({
                "seed": seed, "subject": subject, "fft_mae_bpm": e1_subject[subject],
                "cnn_mae_bpm": subject_row["mae_bpm"],
                "delta_cnn_minus_fft_bpm": subject_row["mae_bpm"] - e1_subject[subject],
            })
    paired_frame = pd.DataFrame(paired)
    paired_frame.to_csv(out / "tables" / "paired_subject_deltas.csv", index=False, encoding="utf-8-sig")
    return {"overall": rows, "paired_rows": paired}


def plot_training(cfg: dict) -> None:
    out = Path(cfg["project"]["output_dir"])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for variant, style in (("A0", "-"), ("A3", "--")):
        for seed in cfg["training"]["seeds"]:
            path = out / "runs" / f"{variant}_seed{seed}" / "training_log.csv"
            if not path.is_file():
                continue
            frame = pd.read_csv(path)
            label = f"{variant}, seed {seed}"
            axes[0].plot(frame.epoch, frame.train_loss, style, lw=1.4, label=label)
            axes[1].plot(frame.epoch, frame.val_mae_macro_bpm, style, lw=1.4, label=label)
    axes[0].set(xlabel="Epoch", ylabel="Training loss", title="Training loss")
    axes[1].set(xlabel="Epoch", ylabel="Validation MAE_macro (BPM)", title="Checkpoint selection metric")
    for ax in axes:
        ax.grid(alpha=.25)
    axes[1].legend(fontsize=8, ncol=2)
    fig.tight_layout()
    _save(fig, out / "figures" / "learning_curves_v2.png")


def plot_core_results(cfg: dict) -> None:
    out = Path(cfg["project"]["output_dir"])
    table = pd.read_csv(out / "tables" / "overall_results_v2.csv")
    fig, ax = plt.subplots(figsize=(8, 4.6))
    yerr = table.mae_macro_std_bpm.fillna(0)
    ax.bar(table.method, table.mae_macro_mean_bpm, yerr=yerr, color=[COLORS.get(x, "#777777") for x in table.method], capsize=4)
    ax.axhline(7, color="#222222", ls="--", lw=1, label="Mục tiêu 7 BPM")
    ax.set(ylabel="Test MAE_macro (BPM)", title="So sánh trên cùng manifest v2")
    ax.grid(axis="y", alpha=.25); ax.legend()
    _save(fig, out / "figures" / "overall_mae_macro.png")
    pred = pd.read_csv(out / "runs" / "A0_seed42" / "test_predictions.csv")
    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(pred.hr_ref_bpm, pred.hr_pred_bpm, s=7, alpha=.25, color=COLORS["A0"])
    limits = [min(pred.hr_ref_bpm.min(), pred.hr_pred_bpm.min()), max(pred.hr_ref_bpm.max(), pred.hr_pred_bpm.max())]
    ax.plot(limits, limits, color="black", lw=1)
    ax.set(xlabel="HR_ref từ ECG (BPM)", ylabel="CNN dự đoán (BPM)", title="Seed 42 cố định trên test")
    ax.grid(alpha=.2)
    _save(fig, out / "figures" / "scatter_identity.png")
    error = pred.hr_pred_bpm - pred.hr_ref_bpm
    mean = (pred.hr_pred_bpm + pred.hr_ref_bpm) / 2
    bias, sd = error.mean(), error.std(ddof=1)
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.scatter(mean, error, s=7, alpha=.22, color=COLORS["A0"])
    ax.axhline(bias, color="black", lw=1.2, label=f"Bias {bias:.2f} BPM")
    ax.axhline(bias + 1.96 * sd, color="#777777", ls="--", lw=1)
    ax.axhline(bias - 1.96 * sd, color="#777777", ls="--", lw=1)
    ax.set(xlabel="Trung bình HR_ref và dự đoán (BPM)", ylabel="Dự đoán - HR_ref (BPM)", title="Bland-Altman mô tả, có đo lặp/chồng lấn")
    ax.legend(); ax.grid(alpha=.2)
    _save(fig, out / "figures" / "bland_altman_v2.png")
    subject = pred.groupby("subject").apply(lambda g: np.mean(np.abs(g.error_bpm)), include_groups=False)
    condition = pred.groupby("condition").apply(lambda g: np.mean(np.abs(g.error_bpm)), include_groups=False)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].bar(subject.index, subject.values, color="#4e79a7")
    axes[0].set(ylabel="MAE pooled (BPM)", title="Theo người")
    axes[1].bar(condition.index, condition.values, color="#f28e2b")
    axes[1].set(ylabel="MAE pooled (BPM)", title="Theo điều kiện")
    for ax in axes: ax.grid(axis="y", alpha=.2)
    fig.tight_layout()
    _save(fig, out / "figures" / "error_by_subject_condition.png")
    timeline = pred[pred.subject.eq("S14")].sort_values("t_start_s").head(180)
    fig, ax = plt.subplots(figsize=(11, 4))
    ax.plot(timeline.t_start_s, timeline.hr_ref_bpm, label="HR_ref", lw=1.6)
    ax.plot(timeline.t_start_s, timeline.hr_pred_bpm, label="CNN seed 42", lw=1.2)
    ax.set(xlabel="Thời gian từ đầu bản ghi (s)", ylabel="BPM", title="S14, 180 cửa sổ đầu tiên theo quy tắc cố định")
    ax.legend(); ax.grid(alpha=.2)
    _save(fig, out / "figures" / "timeline_s14_fixed.png")


def plot_failure_case(cfg: dict) -> dict:
    out = Path(cfg["project"]["output_dir"])
    metadata, arrays, _ = load_processed(cfg)
    validation = pd.read_csv(out / "runs" / "A0_seed42" / "validation_predictions.csv")
    row = validation.loc[validation.error_bpm.abs().idxmax()]
    meta_row = metadata.loc[metadata.window_id.eq(row.window_id)].iloc[0]
    window = arrays["bvp_normalized"][int(meta_row.window_index)]
    fs = cfg["preprocessing"]["fs_bvp"]
    n_fft = cfg["baselines"]["fft_n"]
    freqs = np.fft.rfftfreq(n_fft, 1 / fs)
    power = np.abs(np.fft.rfft(window * np.hanning(len(window)), n_fft)) ** 2
    raw_path = Path(cfg["project"]["raw_data_dir"]) / row.subject / f"{row.subject}.pkl"
    raw = load_subject(raw_path)
    ecg = np.asarray(raw["signal"]["chest"]["ECG"], dtype=float).ravel()
    ecg_f, _ = filter_continuous(ecg, cfg["preprocessing"]["fs_ecg"], cfg["preprocessing"]["ecg_band_hz"], cfg["preprocessing"]["butterworth_order"])
    peaks, _ = detect_r_peaks(ecg_f, cfg["preprocessing"]["fs_ecg"], cfg["qrs"])
    e0 = int(np.floor(row.t_start_s * cfg["preprocessing"]["fs_ecg"] + 1e-9))
    e1 = int(np.floor(row.t_end_s * cfg["preprocessing"]["fs_ecg"] + 1e-9))
    local_peaks = peaks[(peaks >= e0) & (peaks < e1)]
    fig, axes = plt.subplots(3, 1, figsize=(10, 8))
    axes[0].plot(np.arange(len(window)) / fs, window, lw=1)
    axes[0].set(ylabel="BVP z-score", title=f"Failure case chọn trên validation: {row.window_id}")
    band = (freqs >= cfg["baselines"]["fft_band_hz"][0]) & (freqs <= cfg["baselines"]["fft_band_hz"][1])
    axes[1].plot(freqs[band] * 60, power[band], lw=1)
    axes[1].axvline(row.hr_ref_bpm, color="black", ls="--", label=f"HR_ref {row.hr_ref_bpm:.1f}")
    axes[1].set(xlabel="BPM", ylabel="Power", title=f"CNN {row.hr_pred_bpm:.1f} BPM; |error| {abs(row.error_bpm):.1f} BPM")
    axes[1].legend()
    t = np.arange(e0, e1) / cfg["preprocessing"]["fs_ecg"]
    axes[2].plot(t, ecg_f[e0:e1], lw=.7)
    axes[2].scatter(local_peaks / cfg["preprocessing"]["fs_ecg"], ecg_f[local_peaks], s=18, color="#e15759", label="R peaks")
    axes[2].set(xlabel="Thời gian (s)", ylabel="ECG lọc", title="ECG 5–25 Hz và R-peaks tham chiếu")
    axes[2].legend()
    fig.tight_layout()
    _save(fig, out / "figures" / "failure_case_validation_fixed.png")
    info = {"selection_rule": "largest absolute error on validation for fixed seed 42", **row.to_dict()}
    dump_json(out / "audit" / "failure_case_selection.json", info)
    del raw, ecg, ecg_f
    gc.collect()
    return info


def build_qc_selection(cfg: dict) -> pd.DataFrame:
    metadata, _, _ = load_processed(cfg)
    audit_path = Path(cfg["project"]["processed_dir"]) / "window_audit.csv"
    audit = pd.read_csv(audit_path)
    selected = []
    for (_, _), group in metadata.groupby(["subject", "condition"], sort=True):
        indices = np.linspace(0, len(group) - 1, min(5, len(group)), dtype=int)
        sample = group.iloc[indices].copy()
        sample["audit_selection"] = "five_evenly_spaced_accepted"
        selected.append(sample)
    flagged = audit[audit.reason_category.eq("quality")].copy()
    flagged["audit_selection"] = "all_quality_flagged"
    columns = ["window_id", "subject", "split", "t_start_s", "t_end_s", "condition", "purity", "hr_ref_bpm", "n_r_peaks", "r_peak_times_s", "reason", "audit_selection"]
    selection = pd.concat([x[columns] for x in selected] + [flagged[columns]], ignore_index=True)
    path = Path(cfg["project"]["output_dir"]) / "audit" / "qc_review_selection.csv"
    selection.to_csv(path, index=False, encoding="utf-8-sig")
    return selection


def run_analysis(cfg: dict) -> dict:
    tables = build_result_tables(cfg)
    plot_training(cfg)
    plot_core_results(cfg)
    failure = plot_failure_case(cfg)
    selection = build_qc_selection(cfg)
    result = {
        "status": "complete", "created_at": now_iso(),
        "figure_selection": "seed 42 fixed before test inspection; failure case selected on validation only",
        "qc_review_windows": int(len(selection)), "tables": tables, "failure_case": failure,
    }
    dump_json(Path(cfg["project"]["output_dir"]) / "analysis_summary.json", result)
    return result


if __name__ == "__main__":
    from .common import load_config
    print(json.dumps(run_analysis(load_config("configs/final.yaml")), ensure_ascii=False, indent=2))
