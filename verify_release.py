#!/usr/bin/env python3
"""Validate the portable GitHub result-and-plotting release."""

from __future__ import annotations

import hashlib
import csv
import json
import os
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
FORBIDDEN_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".cu", ".cuh",
    ".o", ".obj", ".a", ".so", ".dll", ".dylib", ".exe", ".bin", ".vtk", ".pyc",
    ".tex", ".bib",
}
MAGIC_PREFIXES = (
    b"\x7fELF", b"MZ", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf",
    b"\xce\xfa\xed\xfe", b"\xcf\xfa\xed\xfe",
)
MAX_FILE_BYTES = 100 * 1024 * 1024
EXPECTED_GENERATED = {
    "hist_time_distance.png",
    "paradigm_passage_sim.png",
    "cumulative_time_density.png",
    "ga_7_1.png",
    "Fig4_road_widening_frequency_2m_4m.png",
    "ga_7_2.png",
    "Fig_R2_pareto_front_15d.png",
    "FigR_C1_free_flow_lower_bound.png",
    "Fig_R1_macro_spatial_composite.png",
    "FigR_C5_physical_evacuation_metric_sensitivity.pdf",
    "FigR_C5_physical_optimization_sensitivity.pdf",
    "FigR_C5_nsga2_parameter_sensitivity.pdf",
}
EXPECTED_GENERATED_TABLES = {
    "TableR_C1_macro_runs.csv",
    "TableR_C1_paired_comparison.csv",
    "TableR_C2_15d_representative_solutions.csv",
    "TableR_C2_nsga2_multiseed_runs.csv",
    "TableR_C2_nsga2_multiseed_stability.csv",
    "TableR_C4_scaling_timing_260624.csv",
    "TableR_C5_nsga2_sensitivity_runs.csv",
    "TableR_C5_nsga2_sensitivity_runs_full_N50000_clearance80.csv",
    "TableR_C5_nsga2_sensitivity_summary.csv",
    "TableR_C5_nsga2_sensitivity_summary_full_N50000_clearance80.csv",
    "TableR_C5_physical_optimization_sensitivity_runs.csv",
    "TableR_C5_physical_optimization_sensitivity_runs_full_N50000_clearance80.csv",
    "TableR_C5_physical_optimization_sensitivity_summary.csv",
    "TableR_C5_physical_optimization_sensitivity_summary_full_N50000_clearance80.csv",
    "TableR_C5_physical_optimization_widths.csv",
    "TableR_C5_physical_optimization_widths_full_N50000_clearance80.csv",
    "TableR_C5_physical_sensitivity_paper.csv",
    "TableR_C5_physical_sensitivity_paper_full_N50000_clearance80.csv",
}


def files() -> list[Path]:
    return sorted(
        path for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    )


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    all_files = files()

    for required in (
        ROOT / "plotting" / "run_all.py",
        ROOT / "plotting" / "common_paths.py",
        ROOT / "results",
        ROOT / "figures" / "generated",
    ):
        check(required.exists(), f"missing required path: {required.relative_to(ROOT)}", errors)
    check(not (ROOT / "manuscript").exists(),
          "manuscript directory must not be included in the public release", errors)

    for path in all_files:
        rel = path.relative_to(ROOT)
        check(path.suffix.lower() not in FORBIDDEN_SUFFIXES, f"forbidden suffix: {rel}", errors)
        check(path.stat().st_size < MAX_FILE_BYTES, f"file is at least 100 MiB: {rel}", errors)
        check(not (path.stat().st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)),
              f"executable permission bit: {rel}", errors)
        with path.open("rb") as handle:
            prefix = handle.read(4)
        check(not any(prefix.startswith(magic) for magic in MAGIC_PREFIXES),
              f"native executable/library magic: {rel}", errors)

    text_extensions = {".py", ".md", ".tex"}
    for path in (item for item in all_files if item.suffix.lower() in text_extensions):
        content = path.read_text(encoding="utf-8", errors="replace")
        developer_home = "/" + "home" + "/" + "shyr"
        mounted_root = "/" + "mnt" + "/"
        check(developer_home not in content and mounted_root not in content,
              f"machine-specific absolute path: {path.relative_to(ROOT)}", errors)

    plotting_scripts = sorted((ROOT / "plotting").glob("*.py"))
    for path in plotting_scripts:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        if path.name not in {"common_paths.py"}:
            content = path.read_text(encoding="utf-8")
            check("common_paths" in content, f"script bypasses common_paths: {path.name}", errors)

    generated_figures = [path for path in (ROOT / "figures" / "generated").glob("*") if path.is_file()]
    generated_tables = list((ROOT / "generated" / "tables").glob("*.csv"))
    generated_names = {path.name for path in generated_figures}
    generated_table_names = {path.name for path in generated_tables}
    check(generated_names == EXPECTED_GENERATED,
          f"generated figure set mismatch: extra={sorted(generated_names-EXPECTED_GENERATED)}, missing={sorted(EXPECTED_GENERATED-generated_names)}",
          errors)
    for path in generated_figures:
        check(path.stat().st_size > 0, f"empty generated artifact: {path.name}", errors)
    check(generated_table_names == EXPECTED_GENERATED_TABLES,
          f"generated table set mismatch: extra={sorted(generated_table_names-EXPECTED_GENERATED_TABLES)}, missing={sorted(EXPECTED_GENERATED_TABLES-generated_table_names)}",
          errors)

    physical_done = sorted((ROOT / "results" / "physical_optimization_sensitivity" / "paper_runs_8000").glob("DONE_*"))
    check(len(physical_done) == 39, f"expected 39 physical-sensitivity completed runs, found {len(physical_done)}", errors)
    for path in physical_done:
        meta = json.loads(path.read_text(encoding="utf-8"))
        check(meta.get("crowd") == 8000, f"physical-sensitivity crowd mismatch: {path.name}", errors)

    nsga_done = sorted((ROOT / "results" / "nsga2" / "sensitivity").glob("DONE_*"))
    check(len(nsga_done) == 21, f"expected 21 NSGA-II sensitivity completed runs, found {len(nsga_done)}", errors)
    for path in nsga_done:
        meta = json.loads(path.read_text(encoding="utf-8"))
        check(meta.get("crowd") == 15000, f"NSGA-II sensitivity crowd mismatch: {path.name}", errors)

    protocol_path = ROOT / "results" / "CONTROLLED_SCREEN_PROTOCOL.json"
    check(protocol_path.exists(), "missing controlled-screen protocol", errors)
    if protocol_path.exists():
        protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
        physical_protocol = protocol["physical_parameter_screen_50000"]
        nsga_protocol = protocol["nsga2_parameter_screen_50000"]
        check(physical_protocol.get("clearance_target") == 0.8,
              "50,000-agent physical-screen clearance target is not 0.8", errors)
        check(nsga_protocol.get("clearance_target") == 0.8,
              "50,000-agent NSGA-II clearance target is not 0.8", errors)
        check(nsga_protocol.get("warm_start_count_per_run") == 1,
              "50,000-agent NSGA-II warm-start count is not one", errors)

    physical_50000 = sorted((ROOT / "results" / "physical_optimization_sensitivity" / "runs_50000_clearance80").glob("DONE_*"))
    check(len(physical_50000) == 39,
          f"expected 39 completed 50,000-agent physical-screen runs, found {len(physical_50000)}", errors)
    for path in physical_50000:
        meta = json.loads(path.read_text(encoding="utf-8"))
        check(meta.get("crowd") == 50000 and meta.get("simulator_calls") == 24,
              f"50,000-agent physical-screen metadata mismatch: {path.name}", errors)
        check(meta.get("warm_start_count") == 12,
              f"50,000-agent physical-screen initial population mismatch: {path.name}", errors)

    nsga_50000 = sorted((ROOT / "results" / "nsga2" / "sensitivity_50000_clearance80").glob("DONE_*"))
    check(len(nsga_50000) == 21,
          f"expected 21 completed 50,000-agent NSGA-II runs, found {len(nsga_50000)}", errors)
    for path in nsga_50000:
        meta = json.loads(path.read_text(encoding="utf-8"))
        check(meta.get("crowd") == 50000 and meta.get("simulator_calls") == 240,
              f"50,000-agent NSGA-II metadata mismatch: {path.name}", errors)
        check(meta.get("warm_start_count") == 1,
              f"50,000-agent NSGA-II warm-start mismatch: {path.name}", errors)

    physical_table = ROOT / "generated" / "tables" / "TableR_C5_physical_optimization_sensitivity_summary.csv"
    if physical_table.exists():
        with physical_table.open(newline="", encoding="utf-8") as handle:
            baseline = next(row for row in csv.DictReader(handle) if row["scenario"] == "baseline")
        check(abs(float(baseline["zero_evac_mean"]) - 517.5477058) < 1e-6,
              "physical-sensitivity baseline does not match manuscript value", errors)

    nsga_table = ROOT / "generated" / "tables" / "TableR_C5_nsga2_sensitivity_summary.csv"
    if nsga_table.exists():
        with nsga_table.open(newline="", encoding="utf-8") as handle:
            baseline = next(row for row in csv.DictReader(handle) if row["setting"] == "base")
        check(abs(float(baseline["final_hv_mean"]) - 8834883.766666668) < 1e-6,
              "NSGA-II baseline Hypervolume does not match manuscript value", errors)

    physical_50000_table = ROOT / "generated" / "tables" / "TableR_C5_physical_optimization_sensitivity_summary_full_N50000_clearance80.csv"
    if physical_50000_table.exists():
        with physical_50000_table.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        benefits = [float(row["optimized_improvement_mean_pct"]) for row in rows]
        check(abs(min(benefits) - 14.076947954174784) < 1e-9 and
              abs(max(benefits) - 15.377954573101484) < 1e-9,
              "50,000-agent physical-screen benefit range does not match manuscript", errors)

    physical_50000_widths = ROOT / "generated" / "tables" / "TableR_C5_physical_optimization_widths_full_N50000_clearance80.csv"
    if physical_50000_widths.exists():
        with physical_50000_widths.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        check(all(float(row["R3_mean_width_m"]) == 4.0 and float(row["R13_mean_width_m"]) == 4.0 for row in rows),
              "50,000-agent physical screen does not retain the R3-R13 warm start", errors)

    nsga_50000_table = ROOT / "generated" / "tables" / "TableR_C5_nsga2_sensitivity_summary_full_N50000_clearance80.csv"
    if nsga_50000_table.exists():
        with nsga_50000_table.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        hv = [float(row["final_hv_mean"]) for row in rows]
        jaccard = [float(row["compromise_segment_jaccard"]) for row in rows]
        baseline = next(row for row in rows if row["setting"] == "base")
        check(abs(min(hv) - 4812397.8) < 1e-6 and abs(max(hv) - 4925707.8) < 1e-6 and
              abs(float(baseline["final_hv_mean"]) - 4866968.6) < 1e-6,
              "50,000-agent NSGA-II Hypervolume values do not match manuscript", errors)
        check(abs(min(jaccard) - 0.3571428571428571) < 1e-12 and
              abs(max(jaccard) - 0.55) < 1e-12,
              "50,000-agent NSGA-II Jaccard range does not match manuscript", errors)

    runtime_table = ROOT / "generated" / "tables" / "TableR_C4_scaling_timing_260624.csv"
    if runtime_table.exists():
        with runtime_table.open(newline="", encoding="utf-8") as handle:
            runtime_rows = {int(row["crowd"]): row for row in csv.DictReader(handle)}
        expected_runtime = {5000: 6.55, 10000: 7.485, 20000: 9.89, 50000: 22.115, 100000: 51.325}
        check(set(runtime_rows) == set(expected_runtime), "runtime population sizes do not match manuscript", errors)
        for crowd, expected_mean in expected_runtime.items():
            if crowd in runtime_rows:
                check(abs(float(runtime_rows[crowd]["wall_mean_s"]) - expected_mean) < 1e-9,
                      f"runtime mean mismatch for crowd={crowd}", errors)

    manifest = ROOT / "MANIFEST.sha256"
    if manifest.exists():
        for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            expected, rel_name = line.split("  ", 1)
            target = ROOT / rel_name
            check(target.exists(), f"manifest target missing at line {line_number}: {rel_name}", errors)
            if target.exists():
                actual = hashlib.sha256(target.read_bytes()).hexdigest()
                check(actual == expected, f"hash mismatch: {rel_name}", errors)

    if errors:
        print("RELEASE_VALIDATION_FAIL")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(
        "RELEASE_VALIDATION_PASS "
        f"files={len(all_files)} plotting_scripts={len(plotting_scripts)} "
        f"generated_figures={len(generated_figures)} generated_tables={len(generated_tables)} "
        "manuscript_included=no"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
