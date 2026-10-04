from __future__ import annotations

import argparse
import json

from .baselines import run_baselines
from .common import load_config
from .preprocess import preprocess
from .train import aggregate_runs, smoke_test, train_many, train_one


def parse_seeds(value: str, cfg: dict) -> list[int]:
    if value.lower() == "all":
        return [int(x) for x in cfg["training"]["seeds"]]
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="WESAD Đ18 reproducible final-project pipeline")
    parser.add_argument("command", choices=["preprocess", "baselines", "smoke", "train", "evaluate", "all"])
    parser.add_argument("--config", default="configs/final.yaml")
    parser.add_argument("--variant", default="A0", choices=["A0", "A1", "A2", "A3"])
    parser.add_argument("--seed", default="all", help="all, one seed, or comma-separated seeds")
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    cfg = load_config(args.config)
    seeds = parse_seeds(args.seed, cfg)
    if args.command == "preprocess":
        result = preprocess(cfg)
    elif args.command == "baselines":
        result = run_baselines(cfg)
    elif args.command == "smoke":
        result = smoke_test(cfg)
    elif args.command == "train":
        result = train_many(cfg, args.variant, seeds, resume=not args.no_resume)
    elif args.command == "evaluate":
        results = [train_one(cfg, args.variant, seed, resume=True) for seed in seeds]
        result = aggregate_runs(cfg, args.variant, results)
    else:
        preprocess(cfg)
        run_baselines(cfg)
        smoke_test(cfg)
        result = train_many(cfg, "A0", seeds, resume=not args.no_resume)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
