from __future__ import annotations

import ast
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .common import dump_json, load_config, load_processed, now_iso
from .preprocess import detect_r_peaks, filter_continuous, load_subject, resample_bvp


ROOT = Path(__file__).resolve().parents[1]


def _zscore(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros_like(values)
    mean = float(np.nanmean(values))
    std = float(np.nanstd(values))
    return np.nan_to_num((values - mean) / max(std, 1e-8))


def _subject_signals(cfg: dict, subject: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = Path(cfg["project"]["raw_data_dir"]) / subject / f"{subject}.pkl"
    raw = load_subject(path)
    bvp = resample_bvp(np.asarray(raw["signal"]["wrist"]["BVP"], dtype=float).ravel())
    bvp_f, _ = filter_continuous(
        bvp,
        cfg["preprocessing"]["fs_bvp"],
        cfg["preprocessing"]["bvp_band_hz"],
        cfg["preprocessing"]["butterworth_order"],
    )
    ecg = np.asarray(raw["signal"]["chest"]["ECG"], dtype=float).ravel()
    ecg_f, _ = filter_continuous(
        ecg,
        cfg["preprocessing"]["fs_ecg"],
        cfg["preprocessing"]["ecg_band_hz"],
        cfg["preprocessing"]["butterworth_order"],
    )
    peaks, _ = detect_r_peaks(ecg_f, cfg["preprocessing"]["fs_ecg"], cfg["qrs"])
    return bvp_f, ecg_f, peaks


def _plot_subject(cfg: dict, rows: pd.DataFrame, subject: str, out_dir: Path) -> Path:
    fs_bvp = cfg["preprocessing"]["fs_bvp"]
    fs_ecg = cfg["preprocessing"]["fs_ecg"]
    bvp, ecg, peaks = _subject_signals(cfg, subject)
    selected = rows[(rows.subject == subject) & (rows.audit_selection == "five_evenly_spaced_accepted")]
    selected = selected.sort_values(["condition", "t_start_s"]).reset_index(drop=True)
    fig, axes = plt.subplots(5, 3, figsize=(12, 12), sharex=True)
    condition_order = ["Baseline", "Stress", "Amusement"]
    for col, condition in enumerate(condition_order):
        part = selected[selected.condition == condition].head(5).reset_index(drop=True)
        for row_no in range(5):
            ax = axes[row_no, col]
            if row_no >= len(part):
                ax.axis("off")
                continue
            item = part.iloc[row_no]
            t0, t1 = float(item.t_start_s), float(item.t_end_s)
            b0, b1 = int(round(t0 * fs_bvp)), int(round(t1 * fs_bvp))
            e0, e1 = int(round(t0 * fs_ecg)), int(round(t1 * fs_ecg))
            tb = np.arange(b1 - b0) / fs_bvp
            te = np.arange(e1 - e0) / fs_ecg
            ax.plot(tb, _zscore(bvp[b0:b1]), color="#1565C0", lw=0.9, label="BVP")
            ax.plot(te, _zscore(ecg[e0:e1]) - 4.0, color="#D84315", lw=0.55, alpha=0.8, label="ECG")
            local = peaks[(peaks >= e0) & (peaks < e1)]
            if len(local):
                x = (local - e0) / fs_ecg
                y = _zscore(ecg[e0:e1])[local - e0] - 4.0
                ax.scatter(x, y, marker="x", s=18, color="#111111", linewidths=0.8, label="R-peak")
            ax.set_ylim(-7.5, 4.5)
            ax.grid(alpha=0.18)
            ax.text(0.02, 0.92, f"{t0:.0f}s | HR={float(item.hr_ref_bpm):.1f}", transform=ax.transAxes, fontsize=7, va="top")
            if row_no == 0:
                ax.set_title(condition, fontsize=10, weight="bold")
            if row_no == 4:
                ax.set_xlabel("Thời gian trong cửa sổ (s)", fontsize=8)
            if col == 0:
                ax.set_ylabel(f"Mẫu {row_no + 1}\n(z-score)", fontsize=8)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles[:3], labels[:3], ncol=3, loc="upper center", bbox_to_anchor=(0.5, 0.975), fontsize=8)
    fig.suptitle(f"QC thủ công — {subject}: 5 cửa sổ / điều kiện", fontsize=14, weight="bold", y=0.997)
    fig.text(0.5, 0.01, "BVP và ECG chỉ được chồng sau khi chuẩn hoá để kiểm tra hình dạng; ECG không phải đầu vào mô hình.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0.02, 0.025, 0.98, 0.965))
    path = out_dir / f"{subject}_qc_15_windows.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_flagged(cfg: dict, rows: pd.DataFrame, out_dir: Path) -> list[Path]:
    flagged = rows[rows.audit_selection != "five_evenly_spaced_accepted"].reset_index(drop=True)
    outputs: list[Path] = []
    for page, start in enumerate(range(0, len(flagged), 12), start=1):
        chunk = flagged.iloc[start : start + 12]
        fig, axes = plt.subplots(4, 3, figsize=(12, 10), sharex=True)
        cache: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for ax, (_, item) in zip(axes.ravel(), chunk.iterrows()):
            subject = str(item.subject)
            if subject not in cache:
                cache[subject] = _subject_signals(cfg, subject)
            bvp, _, _ = cache[subject]
            fs = cfg["preprocessing"]["fs_bvp"]
            t0, t1 = float(item.t_start_s), float(item.t_end_s)
            b0, b1 = int(round(t0 * fs)), int(round(t1 * fs))
            x = np.arange(b1 - b0) / fs
            ax.plot(x, _zscore(bvp[b0:b1]), color="#7B1FA2", lw=0.8)
            ax.set_title(f"{subject} {item.condition} | {item.reason}", fontsize=8)
            ax.text(0.02, 0.90, f"t={t0:.0f}s, purity={float(item.purity):.2f}", transform=ax.transAxes, fontsize=7, va="top")
            ax.grid(alpha=0.2)
        for ax in axes.ravel()[len(chunk):]:
            ax.axis("off")
        fig.suptitle(f"Mẫu bị gắn cờ chất lượng — trang {page}", fontsize=14, weight="bold")
        fig.tight_layout(rect=(0.02, 0.02, 0.98, 0.96))
        path = out_dir / f"flagged_quality_page_{page}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        outputs.append(path)
    return outputs


def main() -> None:
    cfg = load_config(ROOT / "configs" / "final.yaml")
    _, _, manifest = load_processed(cfg)
    selection_path = ROOT / "outputs" / "audit" / "qc_review_selection.csv"
    rows = pd.read_csv(selection_path)
    out_dir = ROOT / "outputs" / "figures" / "qc"
    out_dir.mkdir(parents=True, exist_ok=True)
    subject_files = [_plot_subject(cfg, rows, subject, out_dir) for subject in sorted(rows.subject.unique())]
    flagged_files = _plot_flagged(cfg, rows, out_dir)
    accepted = rows[rows.audit_selection == "five_evenly_spaced_accepted"]
    counts = accepted.groupby(["subject", "condition"]).size()
    summary = {
        "status": "complete",
        "created_at": now_iso(),
        "manifest_hash": manifest["manifest_hash"],
        "selection_file": str(selection_path.relative_to(ROOT)),
        "accepted_windows_reviewed": int(len(accepted)),
        "groups_subject_condition": int(len(counts)),
        "minimum_windows_per_subject_condition": int(counts.min()),
        "flagged_windows_plotted": int(len(rows) - len(accepted)),
        "subject_montages": [str(path.relative_to(ROOT)) for path in subject_files],
        "flagged_pages": [str(path.relative_to(ROOT)) for path in flagged_files],
        "review_scope": "visual signal-shape and automated-label plausibility audit; not medical adjudication",
    }
    dump_json(ROOT / "outputs" / "audit" / "qc_audit_summary.json", summary)
    print(summary)


if __name__ == "__main__":
    main()
