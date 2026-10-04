from __future__ import annotations

import torch
from torch import nn


class CnnHr(nn.Module):
    def __init__(self, dropout: float = 0.2, use_batchnorm: bool = True):
        super().__init__()
        layers: list[nn.Module] = []
        specs = [(1, 16, 7, 2, 3), (16, 32, 5, 2, 2), (32, 64, 3, 2, 1)]
        for source, target, kernel, stride, padding in specs:
            layers.append(nn.Conv1d(source, target, kernel, stride, padding, bias=False))
            if use_batchnorm:
                layers.append(nn.BatchNorm1d(target))
            layers.append(nn.ReLU())
        self.features = nn.Sequential(*layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.head = nn.Sequential(
            nn.Flatten(), nn.Dropout(dropout), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.head(self.pool(self.features(x)))


def count_trainable(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)


def make_model(cfg: dict, variant: str) -> CnnHr:
    use_batchnorm = variant != "A2"
    model = CnnHr(dropout=float(cfg["training"]["dropout"]), use_batchnorm=use_batchnorm)
    expected = 11153 if use_batchnorm else 10929
    actual = count_trainable(model)
    if actual != expected:
        raise AssertionError(f"Parameter count {actual} != expected {expected}")
    return model


def input_key_for_variant(variant: str) -> str:
    return "bvp_filtered" if variant == "A1" else "bvp_normalized"


def loss_for_variant(cfg: dict, variant: str) -> nn.Module:
    if variant == "A3":
        return nn.MSELoss(reduction="mean")
    return nn.HuberLoss(delta=float(cfg["training"]["huber_delta_bpm"]), reduction="mean")
