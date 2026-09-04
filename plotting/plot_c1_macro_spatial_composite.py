#!/usr/bin/env python3
"""Draw the combined spatial and temporal macro-verification figure."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common_paths import C1_PAIRED_RUNS, GENERATED_DATA, GENERATED_FIGURES

DATA = GENERATED_DATA / "c1_macro"
if not (DATA / "initial_position_median_5m_baseline.csv").exists():
    DATA = DERIVED / "c1_macro"
OUTPUT = GENERATED_FIGURES / "Fig_R1_macro_spatial_composite.png"
SEEDS = (11, 29, 47, 71, 101)
LAYOUTS = ("baseline", "optimized")
POPULATION = 50_000
CELL_SIZE = 5.0


def rasterize(table: pd.DataFrame, value: str, count: str, nx: int, ny: int) -> np.ndarray:
    array = np.full((ny, nx), np.nan)
    shown = table[table[count] >= 5]
    array[shown.grid_y.to_numpy(int), shown.grid_x.to_numpy(int)] = shown[value].to_numpy(float)
    return array


def load_spatial_arrays() -> tuple[dict[str, np.ndarray], np.ndarray, int, int]:
    tables = {
        layout: pd.read_csv(DATA / f"initial_position_median_5m_{layout}.csv")
        for layout in LAYOUTS
    }
    nx = max(int(table.grid_x.max()) for table in tables.values()) + 1
    ny = max(int(table.grid_y.max()) for table in tables.values()) + 1
    arrays = {
        layout: rasterize(table, "median_evacuation_time", "completed_count", nx, ny)
        for layout, table in tables.items()
    }

    paired = pd.read_csv(DATA / "initial_position_median_5m_paired_change.csv")
    valid = paired[
        (paired.completed_count_baseline >= 5) & (paired.completed_count_optimized >= 5)
    ]
    change = np.full((ny, nx), np.nan)
    change[valid.grid_y.to_numpy(int), valid.grid_x.to_numpy(int)] = (
        valid.median_time_change_s.to_numpy(float)
    )
    return arrays, change, nx, ny


def plot_clearance_curves(axis: plt.Axes, panel_aspect: float) -> None:
    colors = {"baseline": "#D55E00", "optimized": "#0072B2"}
    labels = {"baseline": "Original", "optimized": "Intervention"}
    runs: dict[tuple[str, int], pd.DataFrame] = {}
    for layout in LAYOUTS:
        for seed in SEEDS:
            frame = pd.read_csv(C1_PAIRED_RUNS / layout / f"seed_{seed}" / "alive_series.csv")
            frame.columns = frame.columns.str.strip()
            runs[(layout, seed)] = frame

    # Aggregate at common remaining-population fractions so the horizontal
    # envelope directly represents between-seed variation in clearance time.
    minimum_fraction = max(
        float((frame.alive / POPULATION).min()) for frame in runs.values()
    )
    maximum_fraction = min(
        float((frame.alive / POPULATION).max()) for frame in runs.values()
    )
    fraction_grid = np.linspace(minimum_fraction, maximum_fraction, 1000)

    for layout in LAYOUTS:
        time_curves = []
        for seed in SEEDS:
            frame = runs[(layout, seed)]
            curve = pd.DataFrame({
                "fraction": frame.alive.to_numpy(float) / POPULATION,
                "time": frame.time.to_numpy(float),
            })
            # Use the first time at which each recorded population level is
            # reached, then interpolate clearance time at common fractions.
            curve = (
                curve.groupby("fraction", as_index=False)["time"]
                .min()
                .sort_values("fraction")
            )
            time_curves.append(
                np.interp(
                    fraction_grid,
                    curve.fraction.to_numpy(float),
                    curve.time.to_numpy(float),
                )
            )

        stacked = np.vstack(time_curves)
        lower = np.min(stacked, axis=0)
        upper = np.max(stacked, axis=0)
        median = np.median(stacked, axis=0)
        axis.fill_betweenx(
            fraction_grid,
            lower,
            upper,
            color=colors[layout],
            alpha=0.20,
            linewidth=0,
            zorder=1,
        )
        axis.plot(
            median,
            fraction_grid,
            color=colors[layout],
            lw=1.8,
            label=labels[layout],
            zorder=2,
        )

    for fraction, label in ((0.5, "$t_{50}$"), (0.2, "$t_{80}$"), (0.05, "$t_{95}$")):
        axis.axhline(fraction, color="0.55", ls="--", lw=0.65)
        axis.text(25, fraction + 0.018, label, color="0.35", fontsize=8)
    axis.set(
        title="(d) Population-clearance curves",
        xlabel="Simulation time (s)",
        ylabel="Remaining population fraction",
        xlim=(0, 2000),
        ylim=(0.03, 1.01),
    )
    axis.grid(alpha=0.18)
    axis.legend(frameon=False, fontsize=8, loc="upper right")
    # Match the physical height-to-width ratio of the three spatial panels.
    axis.set_box_aspect(panel_aspect)


def main() -> None:
    arrays, change, nx, ny = load_spatial_arrays()
    values = np.concatenate([array[np.isfinite(array)] for array in arrays.values()])
    vmin, vmax = np.quantile(values, [0.01, 0.99])
    change_limit = float(np.nanquantile(np.abs(change), 0.98))
    extent = (0, nx * CELL_SIZE, 0, ny * CELL_SIZE)

    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
    })
    fig = plt.figure(figsize=(12.0, 12.8))
    outer = fig.add_gridspec(
        2, 2, left=0.065, right=0.95, bottom=0.055, top=0.965,
        wspace=0.18, hspace=0.10,
    )

    def panel(spec, show_colorbar: bool) -> tuple[plt.Axes, plt.Axes]:
        inner = spec.subgridspec(1, 2, width_ratios=(1.0, 0.052), wspace=0.035)
        axis = fig.add_subplot(inner[0, 0])
        color_axis = fig.add_subplot(inner[0, 1])
        if not show_colorbar:
            color_axis.set_axis_off()
        return axis, color_axis

    ax_a, color_a = panel(outer[0, 0], show_colorbar=True)
    ax_b, color_b = panel(outer[0, 1], show_colorbar=True)
    ax_c, color_c = panel(outer[1, 0], show_colorbar=True)
    ax_d, blank_d = panel(outer[1, 1], show_colorbar=False)

    titles = {
        "baseline": "(a) Original layout",
        "optimized": "(b) Representative intervention",
    }
    heatmap = None
    for axis, layout in ((ax_a, "baseline"), (ax_b, "optimized")):
        heatmap = axis.imshow(
            arrays[layout], origin="lower", cmap="viridis", vmin=vmin, vmax=vmax,
            extent=extent, interpolation="nearest",
        )
        axis.set(
            title=titles[layout], xlabel="x (m)",
            ylabel="y (m)" if layout == "baseline" else "",
        )
        axis.set_aspect("equal")
    spatial_bar_a = fig.colorbar(heatmap, cax=color_a)
    spatial_bar_b = fig.colorbar(heatmap, cax=color_b)
    for spatial_bar in (spatial_bar_a, spatial_bar_b):
        spatial_bar.ax.tick_params(labelsize=7)
        spatial_bar.ax.set_title("Time (s)", fontsize=8, pad=5)

    delta_map = ax_c.imshow(
        change, origin="lower", cmap="RdBu_r", vmin=-change_limit, vmax=change_limit,
        extent=extent, interpolation="nearest",
    )
    ax_c.set(
        title="(c) Paired change: intervention minus original",
        xlabel="x (m)", ylabel="y (m)",
    )
    ax_c.set_aspect("equal")
    change_bar = fig.colorbar(delta_map, cax=color_c)
    change_bar.ax.tick_params(labelsize=7)
    change_bar.ax.set_title(r"$\Delta t$ (s)", fontsize=8, pad=5)

    plot_clearance_curves(ax_d, panel_aspect=ny / nx)
    fig.canvas.draw()
    for axis, color_axis in ((ax_a, color_a), (ax_b, color_b), (ax_c, color_c)):
        plot_box = axis.get_position()
        color_box = color_axis.get_position()
        color_axis.set_position([color_box.x0, plot_box.y0, color_box.width, plot_box.height])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=350)
    plt.close(fig)


if __name__ == "__main__":
    main()
