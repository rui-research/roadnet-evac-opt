# Validation record

Validation date: 2026-09-06.

The code-and-data release was checked after removal of the manuscript package.

Recorded requirements:

- the repository contains no `manuscript/` directory, TeX source, bibliography,
  compiled paper, or final manuscript image package;
- `figures/generated/` contains exactly the 12 data-derived active figure names;
- the one-command run completes all eleven focused pipelines;
- generated C5 tables reproduce the manuscript's 8,000-agent physical-sensitivity
  values and 15,000-agent optimizer-sensitivity values;
- generated claim-support tables reproduce the 50,000-agent controlled screens
  and runtime-scaling values;
- the 50,000-agent metadata records an 80% clearance target and warm starts,
  distinct from the separately documented 95% paired verification;
- no C/C++/CUDA source, native executable/library, machine-specific source path,
  or file above GitHub's 100 MB limit is present.

Run:

```bash
MPLBACKEND=Agg python3 plotting/run_all.py
python3 verify_release.py
sha256sum -c MANIFEST.sha256
```

The figure and table regeneration run completed successfully with
`ALL_PLOTTING_PIPELINES_PASS count=11`.
