#!/usr/bin/env python3
"""Reproduce the tables behind the 50,000-agent controlled-screen claims."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from common_paths import NSGA2_SENSITIVITY_50000, PHYSICAL_SENSITIVITY_50000


HERE = Path(__file__).resolve().parent
SUFFIX = "_full_N50000_clearance80"


def main() -> None:
    commands = [
        [
            sys.executable,
            str(HERE / "plot_c5_physical_optimization_sensitivity.py"),
            "--input",
            str(PHYSICAL_SENSITIVITY_50000),
            "--suffix",
            SUFFIX,
            "--tables-only",
        ],
        [
            sys.executable,
            str(HERE / "plot_c5_nsga2_sensitivity.py"),
            "--input",
            str(NSGA2_SENSITIVITY_50000),
            "--suffix",
            SUFFIX,
            "--tables-only",
        ],
    ]
    for command in commands:
        subprocess.run(command, check=True, cwd=HERE)
    print("50,000-agent controlled-screen tables regenerated")


if __name__ == "__main__":
    main()
