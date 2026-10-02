# v0.2.3.2 UTF-8 analysis hotfix

Observed after:

```text
CONTINUATION PASS=20 FAIL=0
```

Analysis then failed while writing `analysis/REPORT.md`:

```text
UnicodeEncodeError: 'charmap' codec can't encode character '\u0394'
```

Cause:
Windows/Python selected the local cp1252 text encoding, while the Markdown report
contains Unicode scientific symbols such as `Δ`.

Fix:
- `analyze.py` explicitly writes REPORT.md as UTF-8;
- REPORT.json is also explicitly UTF-8;
- `run_40_analyze.cmd` sets `PYTHONUTF8=1` as a secondary guard;
- `run_recover_after_completed_200k.cmd` runs only analysis and output packing.

Scientific impact: none.

Do NOT rerun `run_all.cmd` after this particular failure. The log proves:

```text
CONTINUATION PASS=20 FAIL=0
```

so the completed 120k/140k/160k/180k/200k states should be reused.
