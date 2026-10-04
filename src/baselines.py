from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .common import dump_json, ensure_dirs, load_processed, now_iso
from .metrics import summarize_predictions


def fft_predict(windows: np.ndarray, fs: int, n_fft: int, low: float, high: float) -> np.ndarray:
    taper = np.hanning(windows.shape[1]).astype(np.float64)
    spectrum = np.abs(np.fft.rfft(windows * taper[None, :], n=n_fft, axis=1)) ** 2
    frequencies = np.fft.rfftfreq(n_fft, d=1.0 / fs)
    mask = (frequencies >= low) & (frequencies <= high)
    if not mask.any():
        raise ValueError("Empty FFT search band")
    indices = np.argmax(spectrum[:, mask], axis=1)
    return 60.0 * frequencies[mask][indices]


def run_baselines(cfg: dict) -> dict:
    ensure_dirs(cfg)
    metadata, arrays, manifest = load_processed(cfg)
    output = Path(cfg["project"]["output_dir"]) / "baselines"
    output.mkdir(parents=True, exist_ok=True)
    train_median = float(metadata.loc[metadata.split.eq("train"), "hr_ref_bpm"].median())
    fft_cfg = cfg["baselines"]
    results = {
        "created_at": now_iso(),
        "config_hash": cfg["_config_hash"],
        "manifest_hash": manifest["manifest_hash"],
        "train_median_bpm": train_median,
        "methods": {},
    }
    for split in ("validation", "test"):
        mask = metadata.split.eq(split).to_numpy()
        base = metadata.loc[mask, ["window_id", "subject", "split", "condition", "hr_ref_bpm"]].reset_index(drop=True)
        e0 = base.copy()
        e0["hr_pred_bpm"] = train_median
        e0.to_csv(output / f"E0_{split}_predictions.csv", index=False, encoding="utf-8-sig")
        e1 = base.copy()
        e1["hr_pred_bpm"] = fft_predict(
            arrays["bvp_normalized"][mask], cfg["preprocessing"]["fs_bvp"],
            int(fft_cfg["fft_n"]), float(fft_cfg["fft_band_hz"][0]), float(fft_cfg["fft_band_hz"][1]),
        )
        e1.to_csv(output / f"E1_{split}_predictions.csv", index=False, encoding="utf-8-sig")
        results["methods"][f"E0_{split}"] = summarize_predictions(e0, "hr_pred_bpm")
        results["methods"][f"E1_{split}"] = summarize_predictions(e1, "hr_pred_bpm")
    results["fft_config"] = {
        "window": "Hann", "n_fft": int(fft_cfg["fft_n"]),
        "search_band_hz": [float(x) for x in fft_cfg["fft_band_hz"]],
        "physical_bin_spacing_hz": 1.0 / cfg["preprocessing"]["window_seconds"],
        "zero_padded_grid_spacing_hz": cfg["preprocessing"]["fs_bvp"] / fft_cfg["fft_n"],
        "zero_padding_adds_information": False,
    }
    dump_json(output / "baseline_metrics.json", results)
    return results
