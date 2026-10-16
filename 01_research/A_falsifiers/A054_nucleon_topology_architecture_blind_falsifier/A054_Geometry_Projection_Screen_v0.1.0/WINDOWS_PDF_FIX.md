# Windows PDF portability hotfix - 2026-10-13

Fixes ReportLab TTFError for the hard-coded Linux-only `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`.

- Selects Windows Segoe UI/Arial, Linux DejaVu, macOS Arial, or ReportLab-provided Bitstream Vera.
- No font file is included or redistributed.
- `run_all.cmd REPORT` regenerates the publication **without** rerunning the 100 Hessian checks.
- PDF and Markdown are given a new UTC timestamp + secure random suffix. Existing published exports are preserved.
- `results/FULL/REPORT_LATEST.json` is a mutable pointer to the latest publication. Science data are unchanged.

If your first FULL run crashed at the font error, after installing the three changed files, run:

```cmd
run_all.cmd REPORT
```

Require in `results/FULL`: `ROWS.jsonl`, `RUN_SUMMARY.json` and `../REFERENCE_OVERLAYS.jsonl`.
Do not copy older packaged `results/` over your locally computed results; the **minimal hotfix ZIP** only replaces scripts and README.

Scientific thresholds, geometries, and A054-v0.5.1 source inputs are unchanged.
