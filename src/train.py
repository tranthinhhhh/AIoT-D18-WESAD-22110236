from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

from .common import canonical_json, dump_json, ensure_dirs, load_processed, now_iso, set_seed, sha256_bytes
from .metrics import sample_mean_std, summarize_predictions
from .model import count_trainable, input_key_for_variant, loss_for_variant, make_model


class WindowDataset(Dataset):
    def __init__(self, x: np.ndarray, y: np.ndarray):
        self.x = torch.from_numpy(np.ascontiguousarray(x[:, None, :], dtype=np.float32))
        self.y = torch.from_numpy(np.ascontiguousarray(y[:, None], dtype=np.float32))

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, index: int):
        return self.x[index], self.y[index]


def variant_hash(cfg: dict, variant: str, manifest_hash: str) -> str:
    payload = {
        "config_hash": cfg["_config_hash"], "manifest_hash": manifest_hash,
        "variant": variant,
        "input": input_key_for_variant(variant),
        "batchnorm": variant != "A2",
        "loss": "MSE" if variant == "A3" else f"Huber_delta_{cfg['training']['huber_delta_bpm']}",
    }
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def predict(model: nn.Module, x: np.ndarray, batch_size: int, device: torch.device) -> np.ndarray:
    model.eval()
    output = []
    tensor = torch.from_numpy(np.ascontiguousarray(x[:, None, :], dtype=np.float32))
    with torch.inference_mode():
        for start in range(0, len(tensor), batch_size):
            output.append(model(tensor[start : start + batch_size].to(device)).cpu().numpy().ravel())
    return np.concatenate(output).astype(np.float64)


def make_prediction_frame(metadata: pd.DataFrame, mask: np.ndarray, prediction: np.ndarray) -> pd.DataFrame:
    frame = metadata.loc[mask, [
        "window_id", "subject", "split", "t_start_s", "t_end_s", "condition", "hr_ref_bpm"
    ]].reset_index(drop=True)
    frame["hr_pred_bpm"] = prediction
    frame["error_bpm"] = frame["hr_pred_bpm"] - frame["hr_ref_bpm"]
    return frame


def capture_rng(generator: torch.Generator) -> dict[str, Any]:
    return {
        "python": random.getstate(), "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(), "generator": generator.get_state(),
    }


def restore_rng(state: dict[str, Any], generator: torch.Generator) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    generator.set_state(state["generator"])


def smoke_test(cfg: dict) -> dict:
    metadata, arrays, manifest = load_processed(cfg)
    generator = set_seed(42, int(cfg["training"]["cpu_threads"]))
    model = make_model(cfg, "A0")
    x = arrays["bvp_normalized"][:8]
    y = metadata["hr_ref_bpm"].to_numpy(dtype=np.float32)[:8]
    tensor_x = torch.from_numpy(x[:, None, :])
    tensor_y = torch.from_numpy(y[:, None])
    criterion = loss_for_variant(cfg, "A0")
    output = model(tensor_x)
    loss = criterion(output, tensor_y)
    loss.backward()
    gradient_finite = all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    subset = metadata.split.eq("train").to_numpy().nonzero()[0][:128]
    overfit = make_model(cfg, "A0")
    optimizer = torch.optim.AdamW(overfit.parameters(), lr=3e-3, weight_decay=0.0)
    sx = torch.from_numpy(arrays["bvp_normalized"][subset, None, :])
    sy = torch.from_numpy(metadata.iloc[subset]["hr_ref_bpm"].to_numpy(dtype=np.float32)[:, None])
    losses = []
    overfit.train()
    for _ in range(120):
        optimizer.zero_grad(set_to_none=True)
        value = criterion(overfit(sx), sy)
        value.backward()
        optimizer.step()
        losses.append(float(value.item()))
    result = {
        "created_at": now_iso(), "manifest_hash": manifest["manifest_hash"],
        "output_shape": list(output.shape), "trainable_parameters": count_trainable(model),
        "loss_finite": bool(torch.isfinite(loss)), "gradient_finite": bool(gradient_finite),
        "overfit_initial_loss": losses[0], "overfit_final_loss": losses[-1],
        "overfit_loss_decreased": losses[-1] < 0.5 * losses[0],
        "generator_state_saved": generator.get_state().numel() > 0,
    }
    out = Path(cfg["project"]["output_dir"]) / "audit" / "smoke_test.json"
    dump_json(out, result)
    if result["output_shape"] != [8, 1] or result["trainable_parameters"] != 11153:
        raise AssertionError("Model shape/parameter smoke test failed")
    if not result["loss_finite"] or not result["gradient_finite"] or not result["overfit_loss_decreased"]:
        raise AssertionError("Learning smoke test failed")
    return result


def train_one(cfg: dict, variant: str, seed: int, resume: bool = True) -> dict:
    if variant not in {"A0", "A1", "A2", "A3"}:
        raise ValueError(f"Unknown variant {variant}")
    ensure_dirs(cfg)
    metadata, arrays, manifest = load_processed(cfg)
    training = cfg["training"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    generator = set_seed(seed, int(training["cpu_threads"]))
    run_dir = Path(cfg["project"]["output_dir"]) / "runs" / f"{variant}_seed{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    best_path, last_path = run_dir / "best.pt", run_dir / "last.pt"
    metric_path, log_path = run_dir / "metrics.json", run_dir / "training_log.csv"
    run_hash = variant_hash(cfg, variant, manifest["manifest_hash"])
    if metric_path.is_file():
        existing = json.loads(metric_path.read_text(encoding="utf-8"))
        if existing.get("status") == "complete" and existing.get("run_hash") == run_hash:
            return existing
    input_key = input_key_for_variant(variant)
    x = arrays[input_key]
    y = metadata["hr_ref_bpm"].to_numpy(dtype=np.float32)
    masks = {name: metadata.split.eq(name).to_numpy() for name in ("train", "validation", "test")}
    dataset = WindowDataset(x[masks["train"]], y[masks["train"]])
    loader = DataLoader(
        dataset, batch_size=int(training["batch_size"]), shuffle=True,
        num_workers=int(training["num_workers"]), generator=generator, drop_last=False,
    )
    model = make_model(cfg, variant).to(device)
    criterion = loss_for_variant(cfg, variant)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=float(training["learning_rate"]), weight_decay=float(training["weight_decay"])
    )
    history: list[dict[str, Any]] = []
    start_epoch, best_metric, best_epoch, stale = 1, float("inf"), 0, 0
    if resume and last_path.is_file():
        checkpoint = torch.load(last_path, map_location=device, weights_only=False)
        if checkpoint.get("run_hash") != run_hash or checkpoint.get("manifest_hash") != manifest["manifest_hash"]:
            raise ValueError(f"Refusing incompatible resume from {last_path}")
        model.load_state_dict(checkpoint["model_state"])
        optimizer.load_state_dict(checkpoint["optimizer_state"])
        history = checkpoint["history"]
        start_epoch = int(checkpoint["epoch"]) + 1
        best_metric = float(checkpoint["best_val_mae_macro_bpm"])
        best_epoch = int(checkpoint["best_epoch"])
        stale = int(checkpoint["stale_epochs"])
        restore_rng(checkpoint["rng_state"], generator)
    training_started = time.perf_counter()
    for epoch in range(start_epoch, int(training["max_epochs"]) + 1):
        epoch_started = time.perf_counter()
        model.train()
        running_loss, count = 0.0, 0
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item()) * len(batch_x)
            count += len(batch_x)
        val_pred = predict(model, x[masks["validation"]], int(training["batch_size"]), device)
        val_frame = make_prediction_frame(metadata, masks["validation"], val_pred)
        val_metrics = summarize_predictions(val_frame, "hr_pred_bpm")
        val_macro = float(val_metrics["mae_macro_bpm"])
        improved = val_macro < best_metric
        if improved:
            best_metric, best_epoch, stale = val_macro, epoch, 0
            torch.save({
                "status": "best", "created_at": now_iso(), "variant": variant, "seed": seed,
                "epoch": epoch, "model_state": model.state_dict(), "run_hash": run_hash,
                "config_hash": cfg["_config_hash"], "manifest_hash": manifest["manifest_hash"],
                "val_mae_macro_bpm": val_macro, "trainable_parameters": count_trainable(model),
            }, best_path)
        else:
            stale += 1
        row = {
            "epoch": epoch, "train_loss": running_loss / count,
            "val_mae_macro_bpm": val_macro, "val_mae_pooled_bpm": val_metrics["pooled"]["mae_bpm"],
            "best_val_mae_macro_bpm": best_metric, "best_epoch": best_epoch,
            "stale_epochs": stale, "epoch_seconds": time.perf_counter() - epoch_started,
        }
        history.append(row)
        pd.DataFrame(history).to_csv(log_path, index=False, encoding="utf-8-sig")
        torch.save({
            "status": "training", "created_at": now_iso(), "variant": variant, "seed": seed,
            "epoch": epoch, "model_state": model.state_dict(), "optimizer_state": optimizer.state_dict(),
            "history": history, "best_val_mae_macro_bpm": best_metric, "best_epoch": best_epoch,
            "stale_epochs": stale, "rng_state": capture_rng(generator), "run_hash": run_hash,
            "config_hash": cfg["_config_hash"], "manifest_hash": manifest["manifest_hash"],
        }, last_path)
        print(f"{variant} seed {seed} epoch {epoch:03d}: loss={row['train_loss']:.4f}, val_macro={val_macro:.3f}, best={best_metric:.3f}", flush=True)
        if stale >= int(training["early_stopping_patience"]):
            break
    checkpoint = torch.load(best_path, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state"])
    split_metrics = {}
    for split in ("validation", "test"):
        pred = predict(model, x[masks[split]], int(training["batch_size"]), device)
        frame = make_prediction_frame(metadata, masks[split], pred)
        frame.to_csv(run_dir / f"{split}_predictions.csv", index=False, encoding="utf-8-sig")
        split_metrics[split] = summarize_predictions(frame, "hr_pred_bpm")
    result = {
        "status": "complete", "completed_at": now_iso(), "variant": variant, "seed": seed,
        "run_hash": run_hash, "config_hash": cfg["_config_hash"], "manifest_hash": manifest["manifest_hash"],
        "input_key": input_key, "loss": "MSE" if variant == "A3" else "Huber",
        "huber_delta_bpm": None if variant == "A3" else float(training["huber_delta_bpm"]),
        "batchnorm": variant != "A2", "trainable_parameters": count_trainable(model),
        "device": str(device), "best_epoch": best_epoch, "epochs_ran": len(history),
        "best_val_mae_macro_bpm": best_metric, "training_seconds_this_invocation": time.perf_counter() - training_started,
        "n_windows": {name: int(mask.sum()) for name, mask in masks.items()},
        "metrics": split_metrics,
    }
    dump_json(metric_path, result)
    return result


def aggregate_runs(cfg: dict, variant: str, results: list[dict]) -> dict:
    fields = ["mae_macro_bpm", "rmse_macro_bpm"]
    aggregate = {
        field: sample_mean_std([float(result["metrics"]["test"][field]) for result in results])
        for field in fields
    }
    for field in ("mae_bpm", "rmse_bpm", "bias_bpm", "pearson_r"):
        aggregate[f"pooled_{field}"] = sample_mean_std([
            float(result["metrics"]["test"]["pooled"][field]) for result in results
        ])
    baseline_path = Path(cfg["project"]["output_dir"]) / "baselines" / "baseline_metrics.json"
    e1 = None
    if baseline_path.is_file():
        baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        e1 = float(baseline["methods"]["E1_test"]["mae_macro_bpm"])
    cnn = aggregate["mae_macro_bpm"]["mean"]
    payload = {
        "status": "complete", "created_at": now_iso(), "variant": variant,
        "seeds": [int(r["seed"]) for r in results], "aggregate_across_seeds": aggregate,
        "fft_mae_macro_bpm": e1,
        "mae_macro_reduction_vs_fft_pct": None if not e1 or e1 <= 0 else 100.0 * (e1 - cnn) / e1,
        "target_mae_le_7_bpm": bool(cnn <= 7.0),
        "target_reduction_ge_20_pct": bool(e1 and e1 > 0 and 100.0 * (e1 - cnn) / e1 >= 20.0),
        "runs": results,
    }
    path = Path(cfg["project"]["output_dir"]) / "runs" / f"{variant}_summary.json"
    dump_json(path, payload)
    return payload


def train_many(cfg: dict, variant: str, seeds: list[int], resume: bool = True) -> dict:
    results = [train_one(cfg, variant, seed, resume=resume) for seed in seeds]
    return aggregate_runs(cfg, variant, results)
