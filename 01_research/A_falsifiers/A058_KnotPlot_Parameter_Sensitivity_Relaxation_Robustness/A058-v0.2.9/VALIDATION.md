# A058-v0.2.9 validation — source and offline simulation

**Status:** SOURCE / CONTRACT / OFFLINE REGRESSION PASS; **real Windows KnotPlot campaign not executed**.

## Version and design

- Instance version `v0.2.9`; exact pinned external SST Falsifier Framework `v1.0.8`.
- Registered population: **271** = 6 reference sectors + 1 independent switch control + 8 slider axes × 33 nondefault multipliers. No 272nd condition was silently added.
- `run_all.cmd BASIC` or `512`: 271 conditions, go checkpoints `32,128,512`.
- `run_all.cmd 2048`: 271 conditions, checkpoints `32,128,512,2048`.
- `run_all.cmd 32768`: deterministically selected **at most 31** from previous 2048/BASIC results; checkpoints `32,128,512,2048,8192,32768`.
- Selection includes qualified reference conditions, one qualified switch control and at most three measured perturbations per axis; selection source hashes and decisions are stored.
- Sector-specific probes quarantine failed or unsupported runtime lanes, with an optional initialized-graphics fallback for R4; no silent exception-to-success conversion.
- Scientific contract explicitly distinguishes **finite-time matched-iteration response** from convergence or stability of an attractor.

## Executed local checks

- `pytest`: **45 PASS** using an isolated Framework-v1.0.8 runtime module mirror (no Windows KnotPlot executable).
- Python `compileall`: PASS.
- Framework-v1.0.8 science, source, gate and report validators: PASS.
- Framework-v1.0.8 preregistration FREEZE + frozen verification **on a temporary copy**: PASS.
- Blind scanner on source: **0 forbidden-term hits**.
- Synthetic heavy-selection regression: **31 distinct selections** when 6 references, 1 control and 3 candidates on each of 8 anonymous axes qualify; preregistered source hashes verified.
- Partial/unsupported-condition analysis simulation: PASS; no false PASS or asymptotic inference.
- LaTeX: `pdflatex -halt-on-error` **PASS**; report template rendered to **3 pages**. This is a preregistration/report template, not real-run results.
- Release hygiene: no `.venv`, caches, native binaries or historical-output trees.
- ZIP central-directory integrity: PASS.

## Not certified here

- The actual KnotPlot Windows-build behavior at the requested modes, particularly any graphics-initialized fallback for R4, has **not** been executed in this environment.
- The C++17 MSVC/pybind11 extension was **not** compiled in this Linux validation; existing source is carried forward and installation builds it on Windows.
- The entire 271-condition budget campaign and the selected heavy condition execution remain **unexecuted** here. Source and mocked regressions do not establish scientifically valid response curves.

## Preservation and caveats

- Framework v1.0.8 is a local validated maintenance candidate built on frozen v1.0.7; only the A058 instance is newly pinned to v1.0.8.
- Old source versions remain separate. Scientific acquisition persists under `campaign/runs/BASIC`, `campaign/runs/2048`, `campaign/runs/32768` and archiving preserves previous same-tier runs; Framework publication artifacts use unique run IDs.
- The shared safe seed has one `fitto mindist` normalization at install only; all conditions start from that identical hashed geometry with Damped + collision avoidance.
- Any fixed-budget geometry is a **transient observation**, never an equilibrium or physically stable vortex claim.
