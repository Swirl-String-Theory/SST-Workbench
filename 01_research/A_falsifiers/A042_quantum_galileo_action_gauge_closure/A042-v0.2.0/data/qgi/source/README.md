# Public paper fallback

If author-level raw population data are unavailable, run:

```bat
run_fetch_qgi_public_pdf.cmd
```

This downloads the public arXiv manuscript to:

```text
data/qgi/source/2502.14535v4.pdf
```

The pipeline then tries, in order:

1. **Fig. 2A population digitization** — extract the plotted blue population markers and
   recompute the phase with the envelope/Hilbert/cubic/direct-fit pipeline. Grade:
   `PUBLISHED_FIGURE2_POPULATION_DIGITIZED`.
2. **Fig. 3A phase-fit digitization** — only if Fig. 2 does not qualify. Grade:
   `PUBLISHED_FIGURE3_DATA_FIT_DIGITIZED`.

Both are public-figure cross-checks and are `CONDITIONAL`. Neither is relabeled as author-level raw data.
