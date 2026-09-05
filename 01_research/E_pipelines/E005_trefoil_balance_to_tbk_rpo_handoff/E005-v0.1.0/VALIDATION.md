# Validation

The package is built against the actual repository interfaces.

Verified v0.4.8 facts:

- package version: `0.4.8`;
- custom API: `sst_blind.multitopology.run_panel`;
- KnotPlot XYZ reader: `sst_blind.io.load_xyz_text`;
- screen config: `configs/panel_extended.json`;
- adaptive spectral configs through `k_max=64`;
- full confirm config: `configs/hr_ladder/05_R5_N720_K16_ROBUST_FULL.json`;
- target normalizes each input to total length `2*pi`.

Verified v0.4.6 facts:

- repository package reports `0.4.6.1`;
- `configs/archive_full.json` exists and has RPO/Floquet enabled;
- CPU/OpenMP is used as the handoff confirmatory backend.

Artifact-runtime tests:

- Python compilation;
- frozen balance-design selftest;
- synthetic 20-run balance output fixture;
- all four handoff modes prepared successfully;
- blind public entries contain no q/h/p or K31/T23 provenance fields;
- selection-lock tamper check;
- arclength-300 provenance copies generated;
- target-contract file-presence logic unit-tested with synthetic target trees.

Real native TBK/RPO execution remains a target-Windows run because it depends on
the target package's compiled native extensions/backends.


## v0.1.1 runtime validation

- scientific `bridge.py` selection logic unchanged from v0.1.0;
- target config paths unchanged;
- candidate modes unchanged;
- batch banners contain no unescaped `>`;
- outer `run_all.cmd` no longer expands `%ERRORLEVEL%` inside parentheses;
- resume requires exact selected-source SHA-256 equality with existing screen;
- DD32 unavailable path falls back to OpenMP without changing selected inputs.
