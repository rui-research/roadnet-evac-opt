"""Regenerate the released data-derived paper figures and support tables."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

from common_paths import GENERATED_DATA, GENERATED_FIGURES, GENERATED_TABLES


HERE = Path(__file__).resolve().parent
PIPELINES = [
    "plot_legacy_evacuation_hist.py",
    "plot_legacy_fundamental_diagram.py",
    "plot_c1_congestion_heatmap.py",
    "plot_legacy_ga_results.py",
    "plot_c1_paired_macro.py",
    "plot_c1_macro_spatial_composite.py",
    "plot_c2_pareto_15d.py",
    "plot_c5_physical_optimization_sensitivity.py",
    "plot_c5_nsga2_sensitivity.py",
    "analyze_c5_50000_clearance80.py",
    "analyze_runtime_scaling.py",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true", help="list pipelines without running")
    parser.add_argument("--only", nargs="*", help="run only named script files")
    args = parser.parse_args()

    selected = args.only or PIPELINES
    unknown = sorted(set(selected) - set(PIPELINES))
    if unknown:
        parser.error(f"unknown pipeline(s): {', '.join(unknown)}")
    if args.list:
        print("\n".join(PIPELINES))
        return 0

    # Matplotlib's PDF backend otherwise embeds the current timestamp.
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

    for directory in (GENERATED_FIGURES, GENERATED_TABLES, GENERATED_DATA):
        directory.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    for index, name in enumerate(selected, 1):
        print(f"[{index:02d}/{len(selected):02d}] {name}", flush=True)
        subprocess.run([sys.executable, str(HERE / name)], check=True, cwd=HERE)
    elapsed = time.monotonic() - started
    print(f"ALL_PLOTTING_PIPELINES_PASS count={len(selected)} elapsed_s={elapsed:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
