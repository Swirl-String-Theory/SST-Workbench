# SST External Falsifier Report Generator v0.1.0

This program is **not** a framework migration. It reads the public, root-level `GATE_LEDGER.json`, `RUN_SUMMARY.json`, `BACKEND_MANIFEST.json`, `DEPENDENCY_CAVEATS.json`, `SOURCE_MANIFEST.json`, etc. It does **not** traverse `private/`, reveal data, or source geometry; it does **not** change a source. All three report outputs are created **outside** the original output tree:

- `<ID>-<version>_FALSIFIER_REPORT.pdf`
- `<ID>-<version>_FALSIFIER_REPORT.tex`
- `<ID>-<version>_EXTERNAL_REPORT_AUDIT.json`

Run on Windows from anywhere:

```cmd
render_report.cmd "C:\...\A054-v0.5.1\<...>-outputs" "C:\workspace\reports" A054 v0.5.1 "Provider-convergent state selection"
```

Alternatively:

```cmd
python report_generator.py --outputs "..." --dest "..." --catalog A054 --version v0.5.1 --title "Provider-convergent state selection"
```

Requires Python 3.10+. Use a working `pdflatex` for a LaTeX PDF; the fallback uses `reportlab` (`python -m pip install reportlab`). The `.tex` is always written, even with the ReportLab backend. The renderer intentionally does not extract arbitrary scientific equations from source trees: missing content is never fabricated. Store scientific equations in the original experiment report or explicitly prepare an additive source supplement.

**Audit semantics:** Source SHA-256 values and the *declared* run-summary/ledger digest match are recorded; the renderer makes no independent claim to have verified the original frozen protocol, forbidden-term commitments, physics, or complete output manifest. Original failure states remain untouched.

**Security and reproducibility:** the program reads only named root-level JSONs; all read source paths are explicit, report destinations inside original outputs are rejected, and no scientific gate calculation is performed in this tool.
