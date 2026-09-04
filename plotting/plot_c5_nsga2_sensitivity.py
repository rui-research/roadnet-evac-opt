#!/usr/bin/env python3
"""Aggregate fixed-budget, multi-seed NSGA-II OFAT experiments."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import GENERATED_FIGURES, GENERATED_TABLES, NSGA2

TABLES = GENERATED_TABLES
FIGURES = GENERATED_FIGURES
TABLES.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)


def classify(tag: str) -> tuple[str, float, float, int, int]:
    name, seed_text = tag.rsplit("_s", 1)
    pop, cx, mut = 40, 0.80, 0.08
    if name.startswith("pop"):
        pop = int(name[3:])
    elif name == "cx060":
        cx = 0.60
    elif name == "cx095":
        cx = 0.95
    elif name == "mut004":
        mut = 0.04
    elif name == "mut016":
        mut = 0.16
    return name, cx, mut, pop, int(seed_text)


def ideal_compromise(front: pd.DataFrame) -> pd.Series:
    spans = (front[["cost", "evac"]].max() - front[["cost", "evac"]].min()).replace(0, 1)
    norm = (front[["cost", "evac"]] - front[["cost", "evac"]].min()) / spans
    return front.loc[(norm.pow(2).sum(axis=1)).idxmin()]


def selected_segments(widths: str) -> set[int]:
    return {i + 1 for i, value in enumerate(ast.literal_eval(widths)) if value > 0}


def mean_pairwise_jaccard(sets: list[set[int]]) -> float:
    values = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            values.append(len(sets[i] & sets[j]) / len(union) if union else 1.0)
    return float(np.mean(values)) if values else np.nan


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=NSGA2 / "sensitivity")
    parser.add_argument(
        "--suffix", default="",
        help="suffix inserted before .csv/.png/.pdf so prior paper artifacts are preserved",
    )
    parser.add_argument(
        "--tables-only", action="store_true",
        help="write run and summary tables without creating a figure",
    )
    args = parser.parse_args()

    def artifact(directory: Path, stem: str, extension: str) -> Path:
        return directory / f"{stem}{args.suffix}.{extension}"

    per_run = []
    for done in sorted(args.input.glob("DONE_*")):
        tag = done.name.removeprefix("DONE_")
        meta = json.loads(done.read_text())
        hv = pd.read_csv(args.input / f"hv_{tag}.csv")
        front = pd.read_csv(args.input / f"pareto_{tag}.csv")
        compromise = ideal_compromise(front)
        final_hv = float(hv.hypervolume.iloc[-1])
        target = 0.95 * final_hv
        calls95 = int(hv.loc[hv.hypervolume >= target, "sim_calls"].iloc[0])
        name, cx, mut, pop, seed = classify(tag)
        per_run.append({
            "tag": tag, "setting": name, "seed": seed, "population": pop,
            "crossover": cx, "mutation_per_gene": mut,
            "simulator_calls": int(meta["simulator_calls"]), "front_size": len(front),
            "final_hv": final_hv, "calls_to_95pct_hv": calls95,
            "compromise_cost_proxy": float(compromise.cost),
            "compromise_evac": float(compromise.evac),
            "compromise_widths": compromise.widths,
        })
    runs = pd.DataFrame(per_run)
    if runs.empty:
        raise SystemExit("No completed sensitivity runs found")
    runs.to_csv(artifact(TABLES, "TableR_C5_nsga2_sensitivity_runs", "csv"), index=False)

    summary_rows = []
    for setting, group in runs.groupby("setting", sort=False):
        sets = [selected_segments(value) for value in group.compromise_widths]
        summary_rows.append({
            "setting": setting,
            "population": int(group.population.iloc[0]),
            "crossover": float(group.crossover.iloc[0]),
            "mutation_per_gene": float(group.mutation_per_gene.iloc[0]),
            "n_seeds": len(group),
            "simulator_calls_per_seed": int(group.simulator_calls.iloc[0]),
            "final_hv_mean": group.final_hv.mean(),
            "final_hv_sd": group.final_hv.std(ddof=1),
            "calls_to_95pct_hv_mean": group.calls_to_95pct_hv.mean(),
            "calls_to_95pct_hv_sd": group.calls_to_95pct_hv.std(ddof=1),
            "compromise_cost_proxy_mean": group.compromise_cost_proxy.mean(),
            "compromise_evac_mean": group.compromise_evac.mean(),
            "compromise_segment_jaccard": mean_pairwise_jaccard(sets),
        })
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(artifact(TABLES, "TableR_C5_nsga2_sensitivity_summary", "csv"), index=False)

    if args.tables_only:
        print(f"processed {len(runs)} runs and {len(summary)} OFAT settings (tables only)")
        return

    plt.style.use("ggplot")
    plt.rcParams.update({
        "font.size": 8.8,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.85))
    panels = [
        ("population", "Population size", [20, 40, 60], "(a)"),
        ("crossover", "Crossover probability", [0.60, 0.80, 0.95], "(b)"),
        ("mutation_per_gene", "Mutation probability", [0.04, 0.08, 0.16], "(c)"),
    ]
    for panel_index, (ax, (column, label, levels, panel_label)) in enumerate(zip(axes, panels)):
        subset = summary[summary[column].isin(levels)].copy()
        # Exclude rows where a different OFAT factor is non-baseline.
        if column != "population": subset = subset[subset.population == 40]
        if column != "crossover": subset = subset[np.isclose(subset.crossover, 0.80)]
        if column != "mutation_per_gene": subset = subset[np.isclose(subset.mutation_per_gene, 0.08)]
        subset = subset.sort_values(column)
        ax.errorbar(subset[column], subset.final_hv_mean, yerr=subset.final_hv_sd,
                    marker="o", capsize=4, linewidth=2)
        ax.set_xlabel(label)
        if panel_index == 0:
            ax.set_ylabel("Final hypervolume")
        ax.yaxis.get_offset_text().set_x(1.0)
        ax.yaxis.get_offset_text().set_ha("right")
        ax.text(-0.10, 1.03, panel_label, transform=ax.transAxes,
                ha="left", va="bottom", fontweight="bold", clip_on=False)
    fig.tight_layout(w_pad=0.8, rect=(0, 0, 1, 0.94))
    fig.savefig(artifact(FIGURES, "FigR_C5_nsga2_parameter_sensitivity", "pdf"), bbox_inches="tight")
    plt.close(fig)
    print(f"processed {len(runs)} runs and {len(summary)} OFAT settings")


if __name__ == "__main__":
    main()
