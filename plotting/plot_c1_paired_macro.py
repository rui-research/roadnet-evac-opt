#!/usr/bin/env python3
"""Aggregate paired C1 95%-clearance experiments into paper-ready artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from common_paths import C1_PAIRED_RUNS, GENERATED_DATA, GENERATED_FIGURES, GENERATED_TABLES

FIGURES = GENERATED_FIGURES
TABLES = GENERATED_TABLES
DATA = GENERATED_DATA / "c1_macro"
SEEDS = (11, 29, 47, 71, 101)
LAYOUTS = ("baseline", "optimized")
POPULATION = 50000
CELL_SIZE = 5.0


def completed_quantile(done_times: np.ndarray, fraction: float) -> float:
    rank = math.ceil(POPULATION * fraction)
    return float(np.partition(done_times, rank - 1)[rank - 1])


def run_metrics(layout: str, seed: int) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    folder = C1_PAIRED_RUNS / layout / f"seed_{seed}"
    record = pd.read_csv(folder / "run_record.csv")
    record.columns = record.columns.str.strip()
    alive = pd.read_csv(folder / "alive_series.csv")
    alive.columns = alive.columns.str.strip()
    done = record[record.state == 0].copy()
    times = done.time.to_numpy(float)
    integral = float(np.trapezoid(alive.alive.to_numpy(float), alive.time.to_numpy(float)))
    free = done[done.free_flow_time_lower_bound > 0].copy()
    delay = free.time - free.free_flow_time_lower_bound
    ratio = free.time / free.free_flow_time_lower_bound
    row = {
        "layout": layout,
        "seed": seed,
        "population": len(record),
        "completed": len(done),
        "final_remaining": int(alive.alive.iloc[-1]),
        "t50_s": completed_quantile(times, 0.50),
        "t80_s": completed_quantile(times, 0.80),
        "t95_s": completed_quantile(times, 0.95),
        "normalized_person_time_to_95_s": integral / POPULATION,
        "median_actual_time_completed_s": float(free.time.median()),
        "p90_actual_time_completed_s": float(free.time.quantile(0.90)),
        "median_free_flow_lower_bound_s": float(free.free_flow_time_lower_bound.median()),
        "p90_free_flow_lower_bound_s": float(free.free_flow_time_lower_bound.quantile(0.90)),
        "median_delay_above_free_flow_s": float(delay.median()),
        "p90_delay_above_free_flow_s": float(delay.quantile(0.90)),
        "median_time_to_free_flow_ratio": float(ratio.median()),
        "p90_time_to_free_flow_ratio": float(ratio.quantile(0.90)),
        "free_flow_bound_violations": int((free.time + 0.2 < free.free_flow_time_lower_bound).sum()),
    }
    done["layout"] = layout
    done["seed"] = seed
    return row, done, alive


def heatmap_table(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["grid_x"] = np.floor(data.start_x / CELL_SIZE).astype(int)
    data["grid_y"] = np.floor(data.start_y / CELL_SIZE).astype(int)
    result = data.groupby(["grid_y", "grid_x"], as_index=False).agg(
        median_evacuation_time=("time", "median"),
        completed_count=("time", "size"),
    )
    result["x_min"] = result.grid_x * CELL_SIZE
    result["y_min"] = result.grid_y * CELL_SIZE
    return result


def write_spatial_tables(all_done: pd.DataFrame) -> None:
    tables = {}
    for layout in LAYOUTS:
        table = heatmap_table(all_done[all_done.layout == layout])
        table.to_csv(DATA / f"initial_position_median_5m_{layout}.csv", index=False)
        tables[layout] = table
    merged = tables["baseline"].merge(
        tables["optimized"], on=["grid_y", "grid_x"], suffixes=("_baseline", "_optimized")
    )
    merged["median_time_change_s"] = (
        merged.median_evacuation_time_optimized - merged.median_evacuation_time_baseline
    )
    merged.to_csv(DATA / "initial_position_median_5m_paired_change.csv", index=False)


def plot_free_flow(all_done: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12.0, 10.0), constrained_layout=True)
    colors = {"baseline": "#D55E00", "optimized": "#0072B2"}
    titles = {"baseline": "(a) Original layout", "optimized": "(b) Representative intervention"}
    hexbins = []
    for axis, layout in zip(axes[0], LAYOUTS):
        data = all_done[(all_done.layout == layout) & (all_done.free_flow_time_lower_bound > 0)]
        hb = axis.hexbin(
            data.free_flow_time_lower_bound,
            data.time,
            gridsize=70,
            bins="log",
            mincnt=1,
            cmap="viridis",
            extent=(0, 520, 0, 2000),
        )
        hexbins.append(hb)
        axis.plot([0, 520], [0, 520], "--", color="crimson", lw=1.8,
                  label="$T_{sim}=T_{LB}$")
        axis.set(xlim=(0, 520), ylim=(0, 2000), title=titles[layout],
                 xlabel="Actual-path free-flow lower bound (s)", ylabel="Simulated evacuation time (s)")
        axis.legend(frameon=False, loc="upper left")
        axis.grid(alpha=0.15)
    colorbar = fig.colorbar(hexbins[-1], ax=axes[0, :], shrink=0.82, pad=0.02)
    colorbar.set_label("log10(count)")

    ratio_grid = np.linspace(1.0, 15.0, 500)
    for layout in LAYOUTS:
        data = all_done[(all_done.layout == layout) & (all_done.free_flow_time_lower_bound > 0)]
        ratio = (data.time / data.free_flow_time_lower_bound).to_numpy(float)
        density = gaussian_kde(ratio, bw_method="scott")(ratio_grid)
        label = "Original" if layout == "baseline" else "Intervention"
        axes[1, 0].plot(ratio_grid, density, color=colors[layout], lw=2.2, label=label)
        axes[1, 0].fill_between(ratio_grid, 0, density, color=colors[layout], alpha=0.10)
    axes[1, 0].set(xlabel="Actual time / free-flow lower bound", ylabel="Probability density",
                xlim=(1, 15))
    axes[1, 0].set_ylim(bottom=0)
    axes[1, 0].set_title("(c) Distribution of relative time above the lower bound")
    axes[1, 0].grid(alpha=0.2); axes[1, 0].legend(frameon=False)

    seed_data = []
    labels = []
    for layout in LAYOUTS:
        for seed in SEEDS:
            data = all_done[
                (all_done.layout == layout)
                & (all_done.seed == seed)
                & (all_done.free_flow_time_lower_bound > 0)
            ]
            seed_data.append((data.time - data.free_flow_time_lower_bound).to_numpy())
            labels.append(f"{layout[0].upper()}{seed}")
    axes[1, 1].boxplot(seed_data, tick_labels=labels, showfliers=False, patch_artist=True)
    axes[1, 1].set(title="(d) Delay distribution by paired seed",
                   xlabel="Layout and seed", ylabel="Delay above free-flow lower bound (s)")
    axes[1, 1].tick_params(axis="x", rotation=45)
    axes[1, 1].grid(axis="y", alpha=0.2)
    fig.savefig(FIGURES / "FigR_C1_free_flow_lower_bound.png", dpi=400, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIGURES.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    rows, done_frames = [], []
    for layout in LAYOUTS:
        for seed in SEEDS:
            row, done, alive = run_metrics(layout, seed)
            rows.append(row); done_frames.append(done)
    runs = pd.DataFrame(rows)
    runs.to_csv(TABLES / "TableR_C1_macro_runs.csv", index=False)

    base = runs[runs.layout == "baseline"].set_index("seed")
    opt = runs[runs.layout == "optimized"].set_index("seed")
    paired = pd.DataFrame(index=SEEDS)
    for metric in ("t50_s", "t80_s", "t95_s", "normalized_person_time_to_95_s"):
        paired[f"baseline_{metric}"] = base[metric]
        paired[f"optimized_{metric}"] = opt[metric]
        paired[f"change_{metric}"] = opt[metric] - base[metric]
        paired[f"improvement_pct_{metric}"] = 100 * (base[metric] - opt[metric]) / base[metric]
    paired.index.name = "seed"
    paired.to_csv(TABLES / "TableR_C1_paired_comparison.csv")

    summary = {}
    for layout in LAYOUTS:
        group = runs[runs.layout == layout]
        summary[layout] = {
            column: {"mean": float(group[column].mean()), "sd": float(group[column].std(ddof=1))}
            for column in ("t50_s", "t80_s", "t95_s", "normalized_person_time_to_95_s",
                           "median_delay_above_free_flow_s", "median_time_to_free_flow_ratio")
        }
    summary["paired_improvement"] = {
        column: {"mean": float(paired[column].mean()), "sd": float(paired[column].std(ddof=1)),
                 "min": float(paired[column].min()), "max": float(paired[column].max())}
        for column in paired.columns if column.startswith("improvement_pct_")
    }
    (DATA / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    all_done = pd.concat(done_frames, ignore_index=True)
    write_spatial_tables(all_done)
    plot_free_flow(all_done)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
