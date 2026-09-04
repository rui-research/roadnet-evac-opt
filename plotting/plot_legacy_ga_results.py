#!/usr/bin/env python3
"""Regenerate the three GA figures active in the manuscript."""

from __future__ import annotations

import ast

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import entropy

from common_paths import GENERATED_FIGURES, LEGACY


data = pd.read_csv(LEGACY / "ga_training_log.csv")
data["widths"] = data.Solution_Widths.apply(ast.literal_eval)


def gene_diversity(series: pd.Series) -> float:
    return float(np.mean(np.std(np.asarray(series.tolist()), axis=0)))


def gene_entropy(series: pd.Series) -> float:
    matrix = np.asarray(series.tolist())
    return float(np.mean([entropy(np.unique(matrix[:, j], return_counts=True)[1])
                          for j in range(matrix.shape[1])]))


grouped = data.groupby("Generation")
stats = grouped.agg(
    mean_fitness=("Final_Fitness", "mean"),
    best_fitness=("Final_Fitness", "min"),
    fitness_sd=("Final_Fitness", "std"),
    gene_diversity=("widths", gene_diversity),
)
entropy_by_generation = grouped.widths.apply(gene_entropy)

plt.style.use("ggplot")
GENERATED_FIGURES.mkdir(parents=True, exist_ok=True)

fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
axes[0].plot(stats.index, stats.mean_fitness, "--", color="tab:red", lw=2, label="Mean fitness")
axes[0].plot(stats.index, stats.best_fitness, color="tab:blue", lw=2, label="Best fitness")
axes[0].fill_between(stats.index, stats.mean_fitness - stats.fitness_sd,
                     stats.mean_fitness + stats.fitness_sd, color="tab:red", alpha=0.18, label="±1 std")
axes[0].set(xlabel="Generation", ylabel="Final fitness", title="Fitness convergence")
axes[0].legend()
scatter = axes[1].scatter(data.Cost_Score, data.Evac_Score, c=data.Generation,
                          cmap="viridis", s=30, alpha=0.8)
axes[1].set(xlabel="Cost score", ylabel="Evacuation score", title="Objective trade-off")
fig.colorbar(scatter, ax=axes[1], label="Generation")
fig.tight_layout()
fig.savefig(GENERATED_FIGURES / "ga_7_1.png", dpi=300, bbox_inches="tight")
plt.close(fig)

matrix = np.vstack(data.widths.to_numpy())
road_ids = np.arange(1, matrix.shape[1] + 1)
fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
for axis, width, color in zip(axes, (2, 4), ("tab:orange", "tab:blue")):
    axis.bar(road_ids, (matrix == width).mean(axis=0), color=color, alpha=0.8)
    axis.set(xlabel="Road index", title=f"Width = {width} m")
    axis.set_xticks(road_ids)
    axis.grid(axis="y")
axes[0].set_ylabel("Selection frequency")
fig.suptitle("Widening preference of road segments", y=1.02)
fig.tight_layout()
fig.savefig(GENERATED_FIGURES / "Fig4_road_widening_frequency_2m_4m.png",
            dpi=600, bbox_inches="tight")
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
axes[0].plot(stats.index, stats.gene_diversity, marker="o", lw=2)
axes[0].set(xlabel="Generation", ylabel="Mean gene-wise standard deviation",
            title="Population diversity")
axes[1].plot(entropy_by_generation.index, entropy_by_generation.values, marker="o", lw=2)
axes[1].set(xlabel="Generation", ylabel="Mean gene entropy",
            title="Discrete gene diversity (entropy)")
fig.tight_layout()
fig.savefig(GENERATED_FIGURES / "ga_7_2.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print("saved ga_7_1.png, Fig4_road_widening_frequency_2m_4m.png, ga_7_2.png")
