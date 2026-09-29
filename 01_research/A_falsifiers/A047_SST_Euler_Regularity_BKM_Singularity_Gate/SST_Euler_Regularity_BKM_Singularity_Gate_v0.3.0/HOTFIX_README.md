# A047 v0.3.0 packaging hotfix — 2026-09-29

This overlay fixes a Windows-only archive-path failure in `sst_bkm/campaign.py`.

The scientific campaign writes BLIND and REVEALED results before archive creation. If a run ended with `ValueError: ... is not in the subpath ...`, do **not** rerun the Euler campaign immediately. After applying this hotfix, run:

```bat
pack_existing_outputs.cmd
```

The helper verifies that the existing BLIND summary/manifest and REVEALED provenance/reveal-map are present, then creates the three standard archives.

The hotfix changes packaging only. Euler evolution, PKLSA ingestion, carrier selection, hash validation, blindness, BKM diagnostics, convergence logic and thresholds are unchanged.
