# Validation record

Validation date: 2026-09-04.

The release was checked against the current formal manuscript source tree.

Recorded requirements:

- `CEUS.tex`, `reference.bib`, and `CEUS.pdf` match the formal manuscript by SHA-256;
- the 21 active `\includegraphics` dependencies exist and match by SHA-256;
- `manuscript/fig/` contains exactly those 21 active files and no stale figures;
- `figures/generated/` contains exactly the 12 data-derived active figure names;
- the one-command run completes all nine focused pipelines;
- generated C5 tables reproduce the manuscript's 8,000-agent physical-sensitivity
  values and 15,000-agent optimizer-sensitivity values;
- no C/C++/CUDA source, native executable/library, machine-specific source path,
  or file above GitHub's 100 MB limit is present.

Run:

```bash
MPLBACKEND=Agg python3 plotting/run_all.py
python3 verify_release.py
sha256sum -c MANIFEST.sha256
```

The figure regeneration run completed successfully with
`ALL_PLOTTING_PIPELINES_PASS count=9`.
