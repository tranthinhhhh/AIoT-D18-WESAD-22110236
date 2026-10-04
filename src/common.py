from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import scipy
import torch
import yaml


ROOT = Path(__file__).resolve().parents[1]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path, block_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(block_size):
            digest.update(block)
    return digest.hexdigest()


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = (ROOT / config_path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    cfg["_config_path"] = str(config_path)
    cfg["_project_root"] = str(ROOT)
    for key in ("raw_data_dir", "processed_dir", "output_dir"):
        cfg["project"][key] = str((ROOT / cfg["project"][key]).resolve())
    cfg["_config_hash"] = sha256_bytes(
        canonical_json({k: v for k, v in cfg.items() if not k.startswith("_")}).encode("utf-8")
    )
    return cfg


def ensure_dirs(cfg: dict[str, Any]) -> None:
    Path(cfg["project"]["processed_dir"]).mkdir(parents=True, exist_ok=True)
    out = Path(cfg["project"]["output_dir"])
    for name in ("baselines", "runs", "figures", "tables", "logs", "audit"):
        (out / name).mkdir(parents=True, exist_ok=True)


def dump_json(path: str | Path, payload: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def environment_info() -> dict[str, Any]:
    return {
        "timestamp": now_iso(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
        "cuda_device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }


def set_seed(seed: int, cpu_threads: int = 1) -> torch.Generator:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(cpu_threads)
    torch.use_deterministic_algorithms(True, warn_only=True)
    return torch.Generator().manual_seed(seed)


def subject_split_map(cfg: dict[str, Any]) -> dict[str, str]:
    return {
        subject: split_name
        for split_name, subjects in cfg["split"].items()
        for subject in subjects
    }


def verify_subject_files(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(cfg["project"]["raw_data_dir"])
    expected = [s for part in cfg["split"].values() for s in part]
    inventory = []
    missing = []
    for subject in expected:
        path = root / subject / f"{subject}.pkl"
        if not path.is_file():
            missing.append(str(path))
            continue
        stat = path.stat()
        inventory.append({
            "subject": subject,
            "path": str(path),
            "bytes": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
        })
    if missing:
        raise FileNotFoundError("Missing WESAD subject files:\n" + "\n".join(missing))
    return inventory


def processed_paths(cfg: dict[str, Any]) -> dict[str, Path]:
    root = Path(cfg["project"]["processed_dir"])
    return {
        "root": root,
        "windows": root / "windows.npz",
        "metadata": root / "metadata.csv",
        "audit": root / "window_audit.csv",
        "summary": root / "preprocessing_summary.json",
        "manifest": root / "manifest.json",
    }


def load_processed(cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, np.ndarray], dict[str, Any]]:
    paths = processed_paths(cfg)
    metadata = pd.read_csv(paths["metadata"])
    with np.load(paths["windows"]) as archive:
        arrays = {key: archive[key] for key in archive.files}
    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    n = len(metadata)
    if not all(len(value) == n for value in arrays.values()):
        raise ValueError("X/y/metadata alignment failure")
    if not metadata["window_id"].is_unique:
        raise ValueError("window_id must be unique")
    expected = subject_split_map(cfg)
    if not metadata.apply(lambda r: expected[r.subject] == r.split, axis=1).all():
        raise ValueError("Subject split mismatch")
    split_sets = [set(metadata.loc[metadata.split.eq(name), "subject"]) for name in cfg["split"]]
    if any(a & b for i, a in enumerate(split_sets) for b in split_sets[i + 1 :]):
        raise ValueError("Subject leakage across splits")
    if not np.isfinite(arrays["bvp_normalized"]).all() or not np.isfinite(metadata["hr_ref_bpm"]).all():
        raise ValueError("Non-finite processed data")
    return metadata, arrays, manifest


def stable_manifest_hash(metadata: pd.DataFrame) -> str:
    columns = [
        "window_id", "subject", "split", "t_start_s", "t_end_s", "condition_id",
        "purity", "hr_ref_bpm", "n_r_peaks", "rr_intervals_s",
    ]
    payload = metadata[columns].to_csv(index=False, lineterminator="\n", float_format="%.10g")
    return sha256_bytes(payload.encode("utf-8"))
