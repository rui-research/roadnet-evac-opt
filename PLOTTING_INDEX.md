# Released figure and table map

The repository does not distribute the manuscript source or final manuscript
assets. The mapping below records the 12 data-derived paper figures retained for
portable regeneration.

## Data-derived paper figures

| Generated figure | Plotting pipeline | Released input |
|---|---|---|
| `paradigm_passage_sim.png` | `plot_legacy_fundamental_diagram.py` | `results/legacy/fundamental_frames/*.csv` |
| `hist_time_distance.png` | `plot_legacy_evacuation_hist.py` | `results/legacy/baseline_run_record.csv` |
| `cumulative_time_density.png` | `plot_c1_congestion_heatmap.py` | `results/compact/congestion_heatmap_downsampled.npz` |
| `ga_7_1.png` | `plot_legacy_ga_results.py` | `results/legacy/ga_training_log.csv` |
| `Fig4_road_widening_frequency_2m_4m.png` | `plot_legacy_ga_results.py` | `results/legacy/ga_training_log.csv` |
| `ga_7_2.png` | `plot_legacy_ga_results.py` | `results/legacy/ga_training_log.csv` |
| `Fig_R2_pareto_front_15d.png` | `plot_c2_pareto_15d.py` | `results/nsga2/main15/` |
| `FigR_C1_free_flow_lower_bound.png` | `plot_c1_paired_macro.py` | `results/c1_macro/paired_runs/` |
| `Fig_R1_macro_spatial_composite.png` | `plot_c1_paired_macro.py`, then `plot_c1_macro_spatial_composite.py` | `results/c1_macro/paired_runs/` |
| `FigR_C5_physical_evacuation_metric_sensitivity.pdf` | `plot_c5_physical_optimization_sensitivity.py` | `results/physical_optimization_sensitivity/paper_runs_8000/` |
| `FigR_C5_physical_optimization_sensitivity.pdf` | `plot_c5_physical_optimization_sensitivity.py` | same 8,000-agent OFAT data |
| `FigR_C5_nsga2_parameter_sensitivity.pdf` | `plot_c5_nsga2_sensitivity.py` | `results/nsga2/sensitivity/` (15,000 agents) |

`plotting/run_all.py` executes these dependencies in a stable order. Outputs are
written to `figures/generated/`.

## Claim-support tables

These two additional analysis pipelines regenerate three groups of numerical
tables supporting the paper without adding unrelated figures:

| Output | Pipeline | Released input |
|---|---|---|
| 50,000-agent physical-screen tables | `analyze_c5_50000_clearance80.py` | `results/physical_optimization_sensitivity/runs_50000_clearance80/` |
| 50,000-agent NSGA-II screen tables | `analyze_c5_50000_clearance80.py` | `results/nsga2/sensitivity_50000_clearance80/` |
| runtime-scaling table | `analyze_runtime_scaling.py` | `results/runtime/scaling_timing_260624.csv` |

The 50,000-agent screens use an 80% clearance stopping target and warm starts.
They are intentionally kept separate from the 95% paired village-scale
verification and do not support an independent-rediscovery claim.
