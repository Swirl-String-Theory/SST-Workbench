# A011 v0.4.1 - scientific report/output binding restoration

Packaging-only successor of immutable v0.4.0. No scientific equation, numerical threshold, source geometry, dataset seal or blind/reveal commitment was changed.

Run `run_all.cmd` directly from this version folder. It runs tests, then only the registered three-source N=64/128 CPU geometry smoke, and renders the full scientific report through the existing qualified Framework v1.0.10 LaTeX report API. No alternate scientific PDF generator is used. `run_all.cmd SELFTEST` runs tests only. Other campaigns are refused.

Output prefix: `A011_Maxwell_SST_Kinetic_Falsifier`; current output: `./A011_Maxwell_SST_Kinetic_Falsifier_v0.4.1_outputs/`. Each rerun retains its predecessor directory under the original run ID. Scientific PDFs and ZIPs are published in `../` with immutable run IDs and SHA-256 sidecars. `LATEST_RUN.json` is a replaceable pointer; `PUBLICATIONS.jsonl` is append-only.

The report binds the unchanged science contract, frozen geometry protocol, exact source manifests, actual gate ledger, measured tables and diagnostic graphs. The G5 parity PASS remains diagnostic; physical claims stay unresolved. No full physical blind/reveal run is claimed.

Requires the existing local workbench datasets/framework, CPython 3.14 + numpy/pytest/matplotlib, the inherited cp314 native binary, and pdflatex. Matplotlib is used only for scientific diagnostic plots and is available in the tested environment. The framework compiler is used for PDF generation. See `provenance/PARENT_V040_*` for unchanged predecessor protocol/source records.
