#!/usr/bin/env python3
"""Analyze direct and optimization-level physical-parameter sensitivity."""
from __future__ import annotations

import ast
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import numpy as np
import pandas as pd

from common_paths import GENERATED_FIGURES, GENERATED_TABLES, PHYSICAL_SENSITIVITY

PARSER = argparse.ArgumentParser()
PARSER.add_argument("--input", type=Path, default=PHYSICAL_SENSITIVITY / "paper_runs_8000")
PARSER.add_argument(
    "--suffix", default="",
    help="suffix inserted before .csv/.png/.pdf so prior paper artifacts are preserved",
)
PARSER.add_argument(
    "--tables-only", action="store_true",
    help="write run and summary tables without creating figures",
)
ARGS = PARSER.parse_args()
RUNS = ARGS.input
TABLES = GENERATED_TABLES
FIGURES = GENERATED_FIGURES
TABLES.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def artifact(directory: Path, stem: str, extension: str) -> Path:
    return directory / f"{stem}{ARGS.suffix}.{extension}"

SCENARIOS = [
    ("baseline", "Baseline", "baseline", 0),
    ("k_m10", r"$k$: -10%", "k", -10),
    ("k_m5", r"$k$: -5%", "k", -5),
    ("k_p5", r"$k$: +5%", "k", 5),
    ("k_p10", r"$k$: +10%", "k", 10),
    ("h_m10", r"$h$: -10%", "h", -10),
    ("h_m5", r"$h$: -5%", "h", -5),
    ("h_p5", r"$h$: +5%", "h", 5),
    ("h_p10", r"$h$: +10%", "h", 10),
    ("rho_m10", r"$\rho_{max}$: -10%", "rho", -10),
    ("rho_m5", r"$\rho_{max}$: -5%", "rho", -5),
    ("rho_p5", r"$\rho_{max}$: +5%", "rho", 5),
    ("rho_p10", r"$\rho_{max}$: +10%", "rho", 10),
]
ORDER = [item[0] for item in SCENARIOS]
LABEL = {item[0]: item[1] for item in SCENARIOS}
PARAMETER = {item[0]: item[2] for item in SCENARIOS}
PERTURBATION = {item[0]: item[3] for item in SCENARIOS}
FIXED_WIDTHS = np.array([0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0], dtype=float)


def parse_widths(value: str) -> np.ndarray:
    widths = np.asarray(ast.literal_eval(value), dtype=float)
    if widths.shape != (15,):
        raise ValueError(f"expected 15 widths, found {widths.shape}: {value}")
    return widths


def ideal_compromise(front: pd.DataFrame) -> pd.Series:
    objectives = front[["cost", "evac"]].astype(float)
    spans = (objectives.max() - objectives.min()).replace(0, 1)
    normalized = (objectives - objectives.min()) / spans
    return front.loc[normalized.pow(2).sum(axis=1).idxmin()]


def set_jaccard(left: np.ndarray, right: np.ndarray) -> float:
    left_set = set(np.flatnonzero(left > 0))
    right_set = set(np.flatnonzero(right > 0))
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else 1.0


def weighted_jaccard(left: np.ndarray, right: np.ndarray) -> float:
    denominator = np.maximum(left, right).sum()
    return float(np.minimum(left, right).sum() / denominator) if denominator else 1.0


def format_plan(widths: np.ndarray) -> str:
    selected = [
        f"R{index + 1}: +{width:g} m"
        for index, width in enumerate(widths)
        if width > 0
    ]
    return "; ".join(selected) if selected else "No widening"


def exact_evaluation(archive: pd.DataFrame, target: np.ndarray) -> pd.Series:
    matches = archive.widths.map(lambda value: np.array_equal(parse_widths(value), target))
    if not matches.any():
        raise ValueError(f"target warm-start vector not found: {target.tolist()}")
    return archive[matches].iloc[0]


records = []
for done in sorted(RUNS.glob("DONE_*")):
    tag = done.name.removeprefix("DONE_")
    scenario, seed_text = tag.rsplit("_s", 1)
    if scenario not in ORDER:
        continue
    seed = int(seed_text)
    metadata = json.loads(done.read_text(encoding="utf-8"))
    archive = pd.read_csv(RUNS / f"evaluations_{tag}.csv")
    front = pd.read_csv(RUNS / f"pareto_{tag}.csv")
    hypervolume = pd.read_csv(RUNS / f"hv_{tag}.csv")
    zero = exact_evaluation(archive, np.zeros(15))
    fixed = exact_evaluation(archive, FIXED_WIDTHS)
    representative = ideal_compromise(front)
    optimized_widths = parse_widths(representative.widths)
    zero_evac = float(zero.evac)
    fixed_evac = float(fixed.evac)
    optimized_evac = float(representative.evac)
    records.append(
        {
            "tag": tag,
            "scenario": scenario,
            "parameter": PARAMETER[scenario],
            "perturbation_pct": PERTURBATION[scenario],
            "seed": seed,
            "crowd": int(metadata["crowd"]),
            "simulator_calls": int(metadata["simulator_calls"]),
            "wall_seconds": float(metadata["wall_seconds"]),
            "front_size": len(front),
            "final_hypervolume": float(hypervolume.hypervolume.iloc[-1]),
            "zero_evac": zero_evac,
            "fixed_cost": float(fixed.cost_proxy),
            "fixed_evac": fixed_evac,
            "fixed_improvement_pct": 100.0 * (zero_evac - fixed_evac) / zero_evac,
            "optimized_cost": float(representative.cost),
            "optimized_evac": optimized_evac,
            "optimized_improvement_pct": 100.0 * (zero_evac - optimized_evac) / zero_evac,
            "optimized_widths": representative.widths,
            "optimized_segments": ",".join(str(i + 1) for i in np.flatnonzero(optimized_widths > 0)),
        }
    )

runs = pd.DataFrame(records)
expected = len(ORDER) * 3
if len(runs) != expected:
    raise SystemExit(f"expected {expected} completed runs, found {len(runs)}")

baseline_zero = runs[runs.scenario == "baseline"].set_index("seed").zero_evac.to_dict()
runs["zero_change_vs_baseline_pct"] = [
    100.0 * (row.zero_evac - baseline_zero[row.seed]) / baseline_zero[row.seed]
    for row in runs.itertuples()
]

baseline_optimized = {
    int(row.seed): parse_widths(row.optimized_widths)
    for row in runs[runs.scenario == "baseline"].itertuples()
}
runs["segment_jaccard_vs_baseline_reoptimized"] = [
    set_jaccard(parse_widths(row.optimized_widths), baseline_optimized[int(row.seed)])
    for row in runs.itertuples()
]
runs["width_jaccard_vs_baseline_reoptimized"] = [
    weighted_jaccard(parse_widths(row.optimized_widths), baseline_optimized[int(row.seed)])
    for row in runs.itertuples()
]
runs["scenario"] = pd.Categorical(runs.scenario, categories=ORDER, ordered=True)
runs = runs.sort_values(["scenario", "seed"]).reset_index(drop=True)
runs.to_csv(artifact(TABLES, "TableR_C5_physical_optimization_sensitivity_runs", "csv"), index=False)

summary = runs.groupby("scenario", observed=True).agg(
    zero_evac_mean=("zero_evac", "mean"),
    zero_evac_sd=("zero_evac", "std"),
    zero_change_mean_pct=("zero_change_vs_baseline_pct", "mean"),
    zero_change_sd_pct=("zero_change_vs_baseline_pct", "std"),
    fixed_improvement_mean_pct=("fixed_improvement_pct", "mean"),
    fixed_improvement_sd_pct=("fixed_improvement_pct", "std"),
    optimized_improvement_mean_pct=("optimized_improvement_pct", "mean"),
    optimized_improvement_sd_pct=("optimized_improvement_pct", "std"),
    optimized_cost_mean=("optimized_cost", "mean"),
    optimized_cost_sd=("optimized_cost", "std"),
    segment_jaccard_mean=("segment_jaccard_vs_baseline_reoptimized", "mean"),
    segment_jaccard_sd=("segment_jaccard_vs_baseline_reoptimized", "std"),
    width_jaccard_mean=("width_jaccard_vs_baseline_reoptimized", "mean"),
    width_jaccard_sd=("width_jaccard_vs_baseline_reoptimized", "std"),
    final_hypervolume_mean=("final_hypervolume", "mean"),
    final_hypervolume_sd=("final_hypervolume", "std"),
).reindex(ORDER).reset_index()
summary["parameter"] = summary.scenario.map(PARAMETER)
summary["perturbation_pct"] = summary.scenario.map(PERTURBATION)
summary.to_csv(artifact(TABLES, "TableR_C5_physical_optimization_sensitivity_summary", "csv"), index=False)

# Paper-facing table: one row per physical-parameter scenario.  The exact plan
# is the run nearest the three-seed mean in standardized cost-improvement space;
# all seed-level exact plans remain available in the runs table.
paper_rows = []
for scenario in ORDER:
    aggregate = summary[summary.scenario == scenario].iloc[0]
    subset = runs[runs.scenario == scenario].copy()
    cost_sd = float(subset.optimized_cost.std()) or 1.0
    improvement_sd = float(subset.optimized_improvement_pct.std()) or 1.0
    distance = (
        ((subset.optimized_cost - subset.optimized_cost.mean()) / cost_sd) ** 2
        + (
            (subset.optimized_improvement_pct - subset.optimized_improvement_pct.mean())
            / improvement_sd
        ) ** 2
    )
    representative = subset.loc[distance.idxmin()]
    representative_widths = parse_widths(representative.optimized_widths)
    paper_rows.append(
        {
            "scenario": scenario,
            "parameter": PARAMETER[scenario],
            "perturbation_pct": PERTURBATION[scenario],
            "zero_evac_mean": aggregate.zero_evac_mean,
            "zero_evac_sd": aggregate.zero_evac_sd,
            "zero_change_mean_pct": aggregate.zero_change_mean_pct,
            "zero_change_sd_pct": aggregate.zero_change_sd_pct,
            "fixed_improvement_mean_pct": aggregate.fixed_improvement_mean_pct,
            "fixed_improvement_sd_pct": aggregate.fixed_improvement_sd_pct,
            "optimized_improvement_mean_pct": aggregate.optimized_improvement_mean_pct,
            "optimized_improvement_sd_pct": aggregate.optimized_improvement_sd_pct,
            "optimized_cost_mean": aggregate.optimized_cost_mean,
            "optimized_cost_sd": aggregate.optimized_cost_sd,
            "representative_seed": int(representative.seed),
            "representative_cost": representative.optimized_cost,
            "representative_improvement_pct": representative.optimized_improvement_pct,
            "representative_plan": format_plan(representative_widths),
            "representative_width_vector_m": representative.optimized_widths,
            "segment_jaccard_mean": aggregate.segment_jaccard_mean,
            "segment_jaccard_sd": aggregate.segment_jaccard_sd,
            "width_jaccard_mean": aggregate.width_jaccard_mean,
            "width_jaccard_sd": aggregate.width_jaccard_sd,
        }
    )
paper = pd.DataFrame(paper_rows)
paper.to_csv(artifact(TABLES, "TableR_C5_physical_sensitivity_paper", "csv"), index=False)

width_rows = []
for scenario in ORDER:
    subset = runs[runs.scenario == scenario]
    matrix = np.vstack([parse_widths(value) for value in subset.optimized_widths])
    record = {"scenario": scenario}
    record.update({f"R{index + 1}_mean_width_m": matrix[:, index].mean() for index in range(15)})
    record.update({f"R{index + 1}_selection_frequency": (matrix[:, index] > 0).mean() for index in range(15)})
    width_rows.append(record)
widths = pd.DataFrame(width_rows)
widths.to_csv(artifact(TABLES, "TableR_C5_physical_optimization_widths", "csv"), index=False)

if ARGS.tables_only:
    print(f"processed {len(runs)} completed physical-sensitivity runs (tables only)")
    raise SystemExit(0)

plt.rcParams.update(
    {
        "font.size": 8.6,
        "axes.labelsize": 9.4,
        "axes.titlesize": 9.8,
        "xtick.labelsize": 8.2,
        "ytick.labelsize": 8.2,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    }
)

# Figure 1: direct sensitivity of the zero-widening evacuation score F_evac.
fig, axes = plt.subplots(1, 3, figsize=(7.25, 3.0), sharex=True, sharey=True)
panels = [
    ("k", r"Pressure coefficient $k$", "(a)"),
    ("h", r"Kernel smoothing length $h$", "(b)"),
    ("rho", r"Upper density threshold $\rho_{\max}$", "(c)"),
]
for ax, (parameter, title, letter) in zip(axes, panels):
    subset = pd.concat(
        [summary[summary.scenario == "baseline"], summary[summary.parameter == parameter]],
        ignore_index=True,
    ).sort_values("perturbation_pct")
    x = subset.perturbation_pct.to_numpy(float)
    y = subset.zero_change_mean_pct.to_numpy(float)
    error = subset.zero_change_sd_pct.fillna(0).to_numpy(float)
    ax.axhline(0, color="0.35", linewidth=0.8)
    ax.axvline(0, color="0.72", linewidth=0.8, linestyle="--")
    ax.errorbar(x, y, yerr=error, color="#2474B5", marker="o", linewidth=1.8, capsize=2.5)
    ax.set_title(title, pad=7)
    ax.set_xticks([-10, -5, 0, 5, 10])
    ax.set_xlabel("Parameter perturbation (%)")
    ax.grid(True, color="0.88", linewidth=0.6)
    ax.text(-0.055, 1.035, letter, transform=ax.transAxes,
            ha="right", va="bottom", fontweight="bold", clip_on=False)
axes[0].set_ylabel(
    "Change in zero-widening\n"
    r"evacuation score $F_{\mathrm{evac}}$ (%)"
)
fig.tight_layout(w_pad=0.8)
fig.savefig(artifact(FIGURES, "FigR_C5_physical_evacuation_metric_sensitivity", "pdf"), bbox_inches="tight")
plt.close(fig)

# Figure 2: final optimization sensitivity, with performance and width vector.
fig = plt.figure(figsize=(7.35, 7.2))
grid = fig.add_gridspec(2, 3, height_ratios=[1.0, 2.0], hspace=0.44, wspace=0.34)
top_axes = [fig.add_subplot(grid[0, index]) for index in range(3)]
for ax, (parameter, title, letter) in zip(top_axes, panels):
    subset = pd.concat(
        [summary[summary.scenario == "baseline"], summary[summary.parameter == parameter]],
        ignore_index=True,
    ).sort_values("perturbation_pct")
    x = subset.perturbation_pct.to_numpy(float)
    ax.errorbar(
        x, subset.fixed_improvement_mean_pct,
        yerr=subset.fixed_improvement_sd_pct.fillna(0),
        marker="s", linewidth=1.6, capsize=2.5, label="Fixed baseline plan",
    )
    ax.errorbar(
        x, subset.optimized_improvement_mean_pct,
        yerr=subset.optimized_improvement_sd_pct.fillna(0),
        marker="o", linewidth=1.6, capsize=2.5, label="Re-optimized plan",
    )
    ax.axhline(0, color="0.4", linewidth=0.8)
    ax.set_title(title, pad=7)
    ax.set_xticks([-10, -5, 0, 5, 10])
    ax.set_xlabel("Parameter perturbation (%)")
    ax.grid(True, color="0.88", linewidth=0.6)
    ax.text(-0.065, 1.055, letter, transform=ax.transAxes,
            ha="right", va="bottom", fontweight="bold", clip_on=False)
top_axes[0].set_ylabel("Evacuation improvement (%)")
top_axes[0].legend(fontsize=7.2, frameon=False, loc="best")

heat = fig.add_subplot(grid[1, :])
width_matrix = widths[[f"R{index}_mean_width_m" for index in range(1, 16)]].to_numpy(float)
cmap = ListedColormap([
    "#F1F7FB",  # 0.0--0.5 m: palest blue
    "#DCEBF4",  # 0.5--1.5 m
    "#A9CFE5",  # 1.5--2.5 m
    "#6FA9CD",  # 2.5--3.5 m
    "#2474B5",  # 3.5--4.5 m: retain the original darkest blue
])
norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5, 4.5], cmap.N)
image = heat.imshow(width_matrix, aspect="auto", cmap=cmap, norm=norm)
heat.set_xticks(np.arange(15), [f"R{index}" for index in range(1, 16)])
heat.set_yticks(np.arange(len(ORDER)), [LABEL[scenario] for scenario in ORDER])
heat.set_xlabel("Candidate road segment")
heat.set_ylabel("Physical-parameter scenario")
heat.text(-0.035, 1.025, "(d)", transform=heat.transAxes,
          ha="right", va="bottom", fontweight="bold", clip_on=False)
for row in range(width_matrix.shape[0]):
    for column in range(width_matrix.shape[1]):
        value = width_matrix[row, column]
        text_color = "white" if value >= 3.5 else "black"
        heat.text(column, row, f"{value:.1f}", ha="center", va="center",
                  fontsize=6.4, color=text_color)
colorbar = fig.colorbar(image, ax=heat, fraction=0.022, pad=0.015,
                        ticks=[0, 1, 2, 3, 4])
colorbar.set_label("Mean selected widening (m)")
fig.subplots_adjust(left=0.125, right=0.94, top=0.94, bottom=0.075)
fig.savefig(artifact(FIGURES, "FigR_C5_physical_optimization_sensitivity", "pdf"), bbox_inches="tight")
plt.close(fig)

print(summary.to_string(index=False))
