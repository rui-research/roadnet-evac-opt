#!/usr/bin/env python3
"""Merge multi-seed NSGA-II fronts and select preference-based representatives."""
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

from common_paths import GENERATED_DATA, GENERATED_FIGURES, GENERATED_TABLES, NSGA2



def nondominated_indices(values: list[tuple[float, float]]) -> list[int]:
    """Indices of points not dominated in a two-objective minimization problem."""
    keep = []
    for i, point in enumerate(values):
        dominated = False
        for j, other in enumerate(values):
            if i == j:
                continue
            if other[0] <= point[0] and other[1] <= point[1] and other != point:
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return keep


def objective_normalization(front: pd.DataFrame) -> pd.DataFrame:
    values = front[["cost", "evac"]]
    spans = (values.max() - values.min()).replace(0, 1)
    return (values - values.min()) / spans


def ideal_compromise(front: pd.DataFrame) -> pd.Series:
    """Return the point nearest the normalized objective-space ideal."""
    norm = objective_normalization(front)
    return front.loc[norm.pow(2).sum(axis=1).idxmin()]


def choose_weighted(front: pd.DataFrame, cost_weight: float) -> pd.Series:
    norm = objective_normalization(front)
    score = cost_weight * norm.cost + (1 - cost_weight) * norm.evac
    return front.loc[score.idxmin()]


def selected_segments(widths: str) -> set[int]:
    return {i + 1 for i, value in enumerate(ast.literal_eval(widths)) if value > 0}


def pairwise_jaccard(sets: list[set[int]]) -> float:
    values = []
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            union = sets[i] | sets[j]
            values.append(len(sets[i] & sets[j]) / len(union) if union else 1.0)
    return float(np.mean(values)) if values else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=NSGA2 / "main15")
    args = parser.parse_args()
    figures, tables, data = GENERATED_FIGURES, GENERATED_TABLES, GENERATED_DATA
    figures.mkdir(exist_ok=True); tables.mkdir(exist_ok=True); data.mkdir(exist_ok=True)

    fronts = []
    run_rows = []
    seed_compromises = []
    for done in sorted(args.input.glob("DONE_main15_s*")):
        tag = done.name.removeprefix("DONE_")
        meta = json.loads(done.read_text())
        front = pd.read_csv(args.input / f"pareto_{tag}.csv")
        front["seed"] = int(tag.rsplit("_s", 1)[1])
        fronts.append(front)
        seed_ideal = ideal_compromise(front)
        seed_compromises.append((int(front.seed.iloc[0]), seed_ideal))
        run_rows.append({
            "tag": tag, "seed": front.seed.iloc[0], "simulator_calls": meta["simulator_calls"],
            "front_size": len(front), "wall_seconds": meta["wall_seconds"],
            "ideal_cost_proxy": float(seed_ideal.cost),
            "ideal_evac": float(seed_ideal.evac),
            "ideal_widths": seed_ideal.widths,
        })
    if not fronts:
        raise SystemExit("No completed main15 runs found")
    candidates = pd.concat(fronts, ignore_index=True).drop_duplicates(["cost", "evac", "widths"])
    F = list(zip(candidates.evac.astype(float), candidates.cost.astype(float)))
    merged = candidates.iloc[nondominated_indices(F)].sort_values(["cost", "evac"]).reset_index(drop=True)
    merged.to_csv(data / "pareto_front_15d_multiseed.csv", index=False)
    pd.DataFrame(run_rows).to_csv(tables / "TableR_C2_nsga2_multiseed_runs.csv", index=False)

    jaccard = pairwise_jaccard([selected_segments(row.widths) for _, row in seed_compromises])
    n_completed = len(seed_compromises)
    pd.DataFrame([{
        "n_optimizer_seeds": len(seed_compromises),
        "mean_pairwise_ideal_segment_jaccard": jaccard,
        "ideal_cost_mean": np.mean([float(row.cost) for _, row in seed_compromises]),
        "ideal_cost_sd": np.std([float(row.cost) for _, row in seed_compromises], ddof=1) if n_completed > 1 else np.nan,
        "ideal_evac_mean": np.mean([float(row.evac) for _, row in seed_compromises]),
        "ideal_evac_sd": np.std([float(row.evac) for _, row in seed_compromises], ddof=1) if n_completed > 1 else np.nan,
    }]).to_csv(tables / "TableR_C2_nsga2_multiseed_stability.csv", index=False)

    norm = objective_normalization(merged)
    ideal = merged.loc[norm.pow(2).sum(axis=1).idxmin()]
    no_intervention = None
    for archive in args.input.glob("evaluations_main15_s*.csv"):
        evaluated = pd.read_csv(archive)
        mask = evaluated.widths.map(lambda x: all(v == 0 for v in ast.literal_eval(x)))
        if mask.any():
            no_intervention = evaluated[mask].iloc[0]
            break
    reps = []
    if no_intervention is not None:
        reps.append(("No intervention", no_intervention.cost_proxy, no_intervention.evac, no_intervention.widths))
    for label, row in [
        ("Cost-priority", choose_weighted(merged, 0.75)),
        ("Ideal-point compromise", ideal),
        ("Evacuation-priority", choose_weighted(merged, 0.25)),
        ("Minimum evacuation score", merged.loc[merged.evac.idxmin()]),
        ("beta=0.1 preference example", merged.loc[(merged.evac + 0.1 * merged.cost).idxmin()]),
    ]:
        reps.append((label, row.cost, row.evac, row.widths))
    representatives = pd.DataFrame(reps, columns=["Preference", "Cost_proxy", "Evac_score", "Widths"])
    representatives["Selected_segments"] = representatives.Widths.map(
        lambda value: ",".join(str(i) for i in sorted(selected_segments(value)))
    )
    representatives.to_csv(tables / "TableR_C2_15d_representative_solutions.csv", index=False)

    # Preserve the original ggplot appearance while enlarging all text for the
    # manuscript. Long labels are repositioned rather than changing the visual
    # language of the original figure.
    plt.style.use("ggplot")
    fig, ax = plt.subplots(figsize=(9.2, 6.6))
    for seed, group in candidates.groupby("seed"):
        ax.scatter(group.cost, group.evac, s=30, alpha=0.35, label=f"seed {seed}")
    completed_seeds = sorted(candidates.seed.unique())
    front_label = (
        f"Seed-{completed_seeds[0]} nondominated approximation"
        if len(completed_seeds) == 1
        else "Merged nondominated approximation"
    )
    ax.plot(merged.cost, merged.evac, "-o", color="crimson", lw=2, ms=4,
            label=front_label)
    ax.scatter([ideal.cost], [ideal.evac], marker="*", s=260, color="gold",
               edgecolor="black", zorder=5, label="Ideal-point compromise")
    styles = {
        "No intervention": ("black", "s"),
        "Cost-priority": ("tab:green", "D"),
        "Ideal-point compromise": ("gold", "*"),
        "Evacuation-priority": ("tab:blue", "P"),
        "Minimum evacuation score": ("tab:red", "X"),
        "beta=0.1 preference example": ("tab:purple", "o"),
    }
    annotation_offsets = {
        "No intervention": (32, 18),
        "Cost-priority": (34, 30),
        "Ideal-point compromise": (35, 42),
        "Evacuation-priority": (28, 48),
        "Minimum evacuation score": (12, 48),
        "beta=0.1 preference example": (-12, -54),
    }
    annotation_halign = {
        "Minimum evacuation score": "right",
        "beta=0.1 preference example": "left",
    }
    for _, row in representatives.iterrows():
        beta_matches_ideal = (
            row.Preference == "beta=0.1 preference example"
            and np.isclose(row.Cost_proxy, ideal.cost)
            and np.isclose(row.Evac_score, ideal.evac)
        )
        color, marker = styles.get(row.Preference, ("gray", "o"))
        if beta_matches_ideal:
            # Retain the original purple marker while leaving the gold star
            # visible at the coincident location.
            ax.scatter([row.Cost_proxy], [row.Evac_score], facecolors="none",
                       edgecolors=color, marker=marker, s=145, linewidths=2.0,
                       zorder=7)
        else:
            ax.scatter([row.Cost_proxy], [row.Evac_score], color=color, marker=marker,
                       s=105 if marker != "*" else 250, edgecolor="black", zorder=6)
        label = row.Preference
        if row.Preference == "Ideal-point compromise":
            label = "Ideal-point compromise"
        if beta_matches_ideal:
            label = r"$\beta=0.1$ example"
        offset = annotation_offsets.get(row.Preference, (5, 5))
        ax.annotate(
            label,
            xy=(row.Cost_proxy, row.Evac_score),
            xytext=offset,
            textcoords="offset points",
            fontsize=15,
            ha=annotation_halign.get(
                row.Preference,
                "left" if offset[0] >= 0 else "right",
            ),
            va="bottom" if offset[1] >= 0 else "top",
            bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": color, "alpha": 0.92},
            arrowprops={
                "arrowstyle": "->",
                "color": color,
                "lw": 1.6,
                "shrinkA": 4,
                "shrinkB": 6,
                "connectionstyle": "arc3,rad=0.08",
            },
            zorder=8,
        )
    ax.set_xlabel(r"Reconstruction cost, $F_{\mathrm{cost}}$ (relative units)", fontsize=18)
    ax.set_ylabel(r"Evacuation score, $F_{\mathrm{evac}}$ (s)", fontsize=18)
    ax.tick_params(axis="both", labelsize=15)
    ax.margins(x=0.07, y=0.15)
    ax.legend(fontsize=13, loc="upper right")
    fig.tight_layout()
    output_paths = [figures / "Fig_R2_pareto_front_15d.png"]
    for output_path in output_paths:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=400, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"merged {len(candidates)} candidates into {len(merged)} nondominated points")


if __name__ == "__main__":
    main()
