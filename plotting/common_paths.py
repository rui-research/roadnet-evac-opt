"""Single source of truth for every plotting script in this release."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LEGACY = RESULTS / "legacy"
FUNDAMENTAL_FRAMES = LEGACY / "fundamental_frames"
C1_PAIRED_RUNS = RESULTS / "c1_macro" / "paired_runs"
NSGA2 = RESULTS / "nsga2"
PHYSICAL_SENSITIVITY = RESULTS / "physical_optimization_sensitivity"
NSGA2_SENSITIVITY_50000 = NSGA2 / "sensitivity_50000_clearance80"
PHYSICAL_SENSITIVITY_50000 = PHYSICAL_SENSITIVITY / "runs_50000_clearance80"
RUNTIME_RESULTS = RESULTS / "runtime"
COMPACT = RESULTS / "compact"

GENERATED_FIGURES = ROOT / "figures" / "generated"
GENERATED_TABLES = ROOT / "generated" / "tables"
GENERATED_DATA = ROOT / "generated" / "data"


def ensure_output_dirs() -> None:
    for directory in (GENERATED_FIGURES, GENERATED_TABLES, GENERATED_DATA):
        directory.mkdir(parents=True, exist_ok=True)


ensure_output_dirs()
