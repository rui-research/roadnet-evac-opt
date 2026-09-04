#!/usr/bin/env python3
"""Aggregate the two-repeat runtime measurements reported in the manuscript."""

from __future__ import annotations

import pandas as pd

from common_paths import GENERATED_TABLES, RUNTIME_RESULTS


def main() -> None:
    raw = pd.read_csv(RUNTIME_RESULTS / "scaling_timing_260624.csv")
    reported = raw[raw["crowd"].isin([5000, 10000, 20000, 50000, 100000])]
    summary = (
        reported.groupby("crowd", as_index=False)
        .agg(
            wall_mean_s=("wall_s", "mean"),
            wall_sd_s=("wall_s", "std"),
            repetitions=("rep", "count"),
        )
        .sort_values("crowd")
    )
    summary.to_csv(GENERATED_TABLES / "TableR_C4_scaling_timing_260624.csv", index=False)
    print(f"runtime table regenerated for {len(summary)} population sizes")


if __name__ == "__main__":
    main()
