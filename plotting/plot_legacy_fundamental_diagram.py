#!/usr/bin/env python3
"""Regenerate the manuscript's merged simulated fundamental diagram."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import FUNDAMENTAL_FRAMES, GENERATED_FIGURES


def binned_median(x: np.ndarray, y: np.ndarray, bins: int = 25) -> tuple[np.ndarray, np.ndarray]:
    edges = np.unique(np.quantile(x, np.linspace(0, 1, bins + 1)))
    centers, medians = [], []
    for index, (left, right) in enumerate(zip(edges[:-1], edges[1:])):
        mask = (x >= left) & (x <= right if index == len(edges) - 2 else x < right)
        if mask.sum() >= 30:
            centers.append(float(np.median(x[mask])))
            medians.append(float(np.median(y[mask])))
    return np.asarray(centers), np.asarray(medians)


frames = []
for path in sorted(FUNDAMENTAL_FRAMES.glob("*.csv"), key=lambda item: int(item.stem)):
    frame = pd.read_csv(path, on_bad_lines="skip")
    frame.columns = frame.columns.str.strip()
    for column in ("State", "Density", "Speed", "Flow"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frames.append(frame.loc[frame.State == 1, ["Density", "Speed", "Flow"]].dropna())

data = pd.concat(frames, ignore_index=True)
data = data[(data.Density >= 0) & (data.Speed >= 0) & (data.Flow >= 0)]
density = data.Density.to_numpy(float) * 2.0
speed = data.Speed.to_numpy(float)
flow = data.Flow.to_numpy(float) * 2.0
indices = np.linspace(0, len(data) - 1, min(30_000, len(data)), dtype=int)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
panels = [
    (axes[0], speed, "Speed–Density Relationship (Merged Results)", "Speed"),
    (axes[1], flow, "Flow–Density Relationship (Merged Results)", "Flow (= speed × density)"),
]
for axis, values, title, ylabel in panels:
    axis.scatter(density[indices], values[indices], color="tab:blue", marker="x",
                 s=12, linewidths=0.8, alpha=0.28)
    xline, yline = binned_median(density, values)
    axis.plot(xline, yline, color="black", linewidth=2.2, label="Merged median")
    axis.set(xlabel="Density", ylabel=ylabel, title=title, xlim=(0, 4.5))
    axis.grid(True, alpha=0.2)
    axis.legend()
axes[0].set_ylim(0, 2.0)
axes[1].set_ylim(0, 2.5)
fig.tight_layout()

GENERATED_FIGURES.mkdir(parents=True, exist_ok=True)
output = GENERATED_FIGURES / "paradigm_passage_sim.png"
fig.savefig(output, dpi=600, bbox_inches="tight")
plt.close(fig)
print(f"saved {output} from {len(data)} released observations")
