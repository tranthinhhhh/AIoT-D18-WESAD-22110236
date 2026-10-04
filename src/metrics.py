from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def _base(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    error = y_pred - y_true
    finite = np.isfinite(y_true) & np.isfinite(y_pred)
    if not finite.all():
        raise ValueError(f"Prediction failures: {int((~finite).sum())}")
    correlation = float(np.corrcoef(y_true, y_pred)[0, 1]) if len(y_true) > 1 else math.nan
    return {
        "n_windows": int(len(y_true)),
        "mae_bpm": float(np.mean(np.abs(error))),
        "rmse_bpm": float(np.sqrt(np.mean(error ** 2))),
        "bias_bpm": float(np.mean(error)),
        "pearson_r": correlation,
        "loa_lower_bpm": float(np.mean(error) - 1.96 * np.std(error, ddof=1)),
        "loa_upper_bpm": float(np.mean(error) + 1.96 * np.std(error, ddof=1)),
        "prediction_failures": 0,
    }


def summarize_predictions(frame: pd.DataFrame, prediction_col: str) -> dict[str, Any]:
    overall = _base(frame["hr_ref_bpm"].to_numpy(), frame[prediction_col].to_numpy())
    subject_rows = []
    for subject, group in frame.groupby("subject", sort=True):
        row = {"subject": subject, **_base(group["hr_ref_bpm"], group[prediction_col])}
        subject_rows.append(row)
    subject_mae = np.asarray([row["mae_bpm"] for row in subject_rows])
    subject_rmse = np.asarray([row["rmse_bpm"] for row in subject_rows])
    condition_rows = []
    for condition, group in frame.groupby("condition", sort=True):
        per_subject = []
        for subject, part in group.groupby("subject", sort=True):
            per_subject.append({"subject": subject, **_base(part["hr_ref_bpm"], part[prediction_col])})
        pooled = _base(group["hr_ref_bpm"], group[prediction_col])
        condition_rows.append({
            "condition": condition,
            "n_subjects": len(per_subject),
            "n_windows": int(len(group)),
            "hr_ref_min_bpm": float(group["hr_ref_bpm"].min()),
            "hr_ref_median_bpm": float(group["hr_ref_bpm"].median()),
            "hr_ref_max_bpm": float(group["hr_ref_bpm"].max()),
            "mae_macro_bpm": float(np.mean([row["mae_bpm"] for row in per_subject])),
            "rmse_macro_bpm": float(np.mean([row["rmse_bpm"] for row in per_subject])),
            "pooled": pooled,
            "by_subject": per_subject,
        })
    return {
        "mae_macro_bpm": float(subject_mae.mean()),
        "rmse_macro_bpm": float(subject_rmse.mean()),
        "n_subjects": int(len(subject_rows)),
        "pooled": overall,
        "by_subject": subject_rows,
        "by_condition": condition_rows,
    }


def sample_mean_std(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std_sample": float(array.std(ddof=1)) if len(array) > 1 else math.nan,
        "values": [float(x) for x in array],
    }
