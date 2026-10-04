from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path

import numpy as np
import torch

from .common import dump_json, load_processed, now_iso
from .model import count_trainable, make_model
from .preprocess import filter_continuous, load_subject, resample_bvp


def timing_summary(milliseconds: list[float]) -> dict:
    values = np.asarray(milliseconds, dtype=float)
    return {
        "n": int(len(values)), "mean_ms": float(values.mean()),
        "median_ms": float(np.median(values)), "p95_ms": float(np.percentile(values, 95)),
        "min_ms": float(values.min()), "max_ms": float(values.max()),
    }


def benchmark(cfg: dict) -> dict:
    torch.set_num_threads(int(cfg["training"]["cpu_threads"]))
    metadata, arrays, manifest = load_processed(cfg)
    run_dir = Path(cfg["project"]["output_dir"]) / "runs" / "A0_seed42"
    checkpoint_path = run_dir / "best.pt"
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model = make_model(cfg, "A0").cpu().eval()
    model.load_state_dict(checkpoint["model_state"])
    test_index = int(np.flatnonzero(metadata.split.eq("test").to_numpy())[0])
    tensor = torch.from_numpy(arrays["bvp_normalized"][test_index][None, None, :].astype(np.float32))
    warmup = int(cfg["benchmark"]["warmup_iterations"])
    measured = int(cfg["benchmark"]["measured_iterations"])
    with torch.inference_mode():
        for _ in range(warmup):
            model(tensor)
        network_times = []
        for _ in range(measured):
            start = time.perf_counter_ns(); model(tensor); stop = time.perf_counter_ns()
            network_times.append((stop - start) / 1e6)
    subject = cfg["split"]["test"][0]
    raw_path = Path(cfg["project"]["raw_data_dir"]) / subject / f"{subject}.pkl"
    raw = load_subject(raw_path)
    raw_bvp = np.asarray(raw["signal"]["wrist"]["BVP"], dtype=np.float64).ravel()
    preprocessing_times = []
    possible_updates = max(1, int(np.floor((len(raw_bvp) / cfg["preprocessing"]["fs_bvp_original"] - cfg["preprocessing"]["window_seconds"]) / cfg["preprocessing"]["stride_seconds"] + 1)))
    for _ in range(2):
        down = resample_bvp(raw_bvp)
        filter_continuous(down, cfg["preprocessing"]["fs_bvp"], cfg["preprocessing"]["bvp_band_hz"], cfg["preprocessing"]["butterworth_order"])
    for _ in range(5):
        start = time.perf_counter_ns()
        down = resample_bvp(raw_bvp)
        filtered, _ = filter_continuous(down, cfg["preprocessing"]["fs_bvp"], cfg["preprocessing"]["bvp_band_hz"], cfg["preprocessing"]["butterworth_order"])
        _ = (filtered - np.nanmean(filtered)) / max(float(np.nanstd(filtered)), cfg["preprocessing"]["zscore_epsilon"])
        stop = time.perf_counter_ns()
        preprocessing_times.append((stop - start) / 1e6)
    preprocessing_per_update = [value / possible_updates for value in preprocessing_times]
    network = timing_summary(network_times)
    pre_whole = timing_summary(preprocessing_times)
    pre_update = timing_summary(preprocessing_per_update)
    result = {
        "status": "complete", "created_at": now_iso(), "manifest_hash": manifest["manifest_hash"],
        "cpu": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown"),
        "os": platform.platform(), "torch": torch.__version__, "dtype": "float32",
        "threads": torch.get_num_threads(), "batch_size": 1,
        "warmup_iterations_network": warmup, "measured_iterations_network": measured,
        "network_only": network,
        "preprocessing_offline_whole_record": {
            **pre_whole, "subject": subject, "record_seconds": len(raw_bvp) / cfg["preprocessing"]["fs_bvp_original"],
            "description": "resample_poly 64->32 Hz, full-record sosfiltfilt 0.5-8 Hz, then normalization; file I/O excluded",
        },
        "preprocessing_amortized_per_2s_update": {**pre_update, "n_updates": possible_updates},
        "end_to_end_additive_offline_estimate_ms": {
            "median": pre_update["median_ms"] + network["median_ms"],
            "p95_conservative_sum": pre_update["p95_ms"] + network["p95_ms"],
        },
        "observation_window_seconds": cfg["preprocessing"]["window_seconds"],
        "update_stride_seconds": cfg["preprocessing"]["stride_seconds"],
        "warning": "Offline amortized preprocessing is not a causal streaming latency measurement; observation and update periods remain 8 s and 2 s.",
        "trainable_parameters": count_trainable(model),
        "checkpoint_bytes": checkpoint_path.stat().st_size,
    }
    dump_json(Path(cfg["project"]["output_dir"]) / "benchmark_cpu.json", result)
    return result


if __name__ == "__main__":
    from .common import load_config
    print(json.dumps(benchmark(load_config("configs/final.yaml")), ensure_ascii=False, indent=2))
