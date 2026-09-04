# Paper figure map

The authoritative source is `manuscript/CEUS.tex`. It contains 21 active figure
references. The commented graphical-abstract placeholder is excluded.

## Data-derived manuscript figures

| Manuscript asset | Plotting pipeline | Released input |
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

`plotting/run_all.py` executes these dependencies in a stable order. The
generated names exactly match the corresponding active manuscript filenames.

## Preserved source/assembled manuscript assets

These nine active figures are preserved as final paper assets and are not
claimed to be regenerated from released numerical data:

| Manuscript asset | Role |
|---|---|
| `shipai_street_view.png` | case-study context |
| `framework.png` | simulation–optimization framework |
| `BFS.png` | navigation-field method illustration |
| `paradigm_obs.png` | empirical relationship cited by the manuscript |
| `shipai_seli.png` | assembled study-area map |
| `Snipaste_2025-12-11_19-43-55.png` | road-network/potential-field layout |
| `simulation_process_1.png` | simulation snapshots, part 1 |
| `simulation_process_2.png` | simulation snapshots, part 2 |
| `micro_reconstructed_area.png` | assembled candidate-road map |
