# Released data inventory

The package contains 476 result/data files (about 88 MiB) selected solely by
the active paper-figure and claim-support pipelines.

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
| `results/nsga2/sensitivity_50000_clearance80/` | controlled scale-up optimizer screen | 50,000 agents; 80% clearance target; 7 settings × 3 seeds; 240 calls per run; one warm-start candidate per run |
| `results/physical_optimization_sensitivity/runs_50000_clearance80/` | controlled scale-up physical screen | 50,000 agents; 80% clearance target; 13 settings × 3 seeds; 24 calls per run; 12-member supplied initial population |
| `results/physical_optimization_sensitivity/warm_starts_15d.json` | provenance for the supplied physical-screen candidates | identifies the R3–R13 candidate retained in the controlled screen |
| `results/runtime/scaling_timing_260624.csv` | runtime-scaling table | two recorded repetitions for each tested population size |
| `results/CONTROLLED_SCREEN_PROTOCOL.json` | machine-readable evidence boundary | distinguishes the 80% warm-started screens from the separate 95% paired verification |

Large native simulator layers are not released. The congestion archive retains
the road mask and aggregated cumulative-density/congestion values needed for a
portable paper-level plot; it is not a byte-for-byte replacement for the native
full-resolution layer export.

No failed or unfinished run is counted as completed evidence. In particular,
the main 15-segment Pareto release contains only the completed seed-11 run.
The 50,000-agent controlled screens preserve every completed run and are
reported as warm-started retention/finite-budget evidence, not as independent
rediscovery or as a causal test of population scale.
