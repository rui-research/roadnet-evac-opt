# Validation record

Validation date: 2026-09-04.

The release was checked against the canonical final CEUS revision supplied on
2026-09-04 and its freshly compiled 45-page PDF.

Recorded requirements:

- `CEUS.tex` and `reference.bib` match the canonical revision by SHA-256, and
  `CEUS.pdf` is freshly compiled from that source;
- the 21 active `\includegraphics` dependencies exist and match by SHA-256;
- `manuscript/fig/` contains exactly those 21 active files and no stale figures;
- `figures/generated/` contains exactly the 12 data-derived active figure names;
- the one-command run completes all eleven focused pipelines;
- generated C5 tables reproduce the manuscript's 8,000-agent physical-sensitivity
  values and 15,000-agent optimizer-sensitivity values;
- generated claim-support tables reproduce the 50,000-agent controlled screens
  and runtime-scaling values;
- the 50,000-agent metadata records an 80% clearance target and warm starts,
  while the manuscript explicitly separates it from the 95% paired verification;
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
