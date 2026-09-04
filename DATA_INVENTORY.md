# Released data inventory

The package contains 254 result/data files (about 86 MiB) selected solely by
the active paper-figure pipelines.

| Data area | Purpose | Scope |
|---|---|---|
| `results/legacy/fundamental_frames/` | simulated fundamental diagram | nine released time-frame CSV files |
| `results/legacy/baseline_run_record.csv` | evacuation-time/distance histograms | completed baseline records |
| `results/legacy/ga_training_log.csv` | GA convergence, trade-off, widening, and diversity | generation-level candidate log |
| `results/compact/congestion_heatmap_downsampled.npz` | cumulative congestion panels | deterministic 8× spatial aggregation of the original 8,000×10,000 grid |
| `results/c1_macro/paired_runs/` | free-flow and spatial/process validation | two layouts × five paired seeds × records and alive series |
| `results/nsga2/main15/` | finite-budget Pareto figure | completed seed-11 metadata, evaluations, and Pareto front |
| `results/nsga2/sensitivity/` | optimizer-parameter sensitivity | 15,000 agents; 7 settings × 3 seeds; DONE, Hypervolume, and Pareto files |
| `results/physical_optimization_sensitivity/paper_runs_8000/` | physical/crowd-model sensitivity | 8,000 agents; 13 settings × 3 seeds; files directly read by the analysis |

Large native simulator layers are not released. The congestion archive retains
the road mask and aggregated cumulative-density/congestion values needed for a
portable paper-level plot; it is not a byte-for-byte replacement for the native
full-resolution layer export.

No failed or unfinished run is counted as completed evidence. In particular,
the main 15-segment Pareto release contains only the completed seed-11 run.
