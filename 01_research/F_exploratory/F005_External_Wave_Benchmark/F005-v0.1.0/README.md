# F005 v0.4.2 — Predictive-power and waveform-family qualification (PATCH)

Project: `01_research/F_exploratory/F005_External_Wave_Benchmark/F005-v0.1.0/`

Current status: **DEVELOPMENT / NOT BLIND / NOT EULER / NOT PKLSA**.

Install by extracting all package contents into the *existing* F005 instance; keep every earlier release and raw source archive. Requirements and step-by-step Windows instructions: `docs/README_FIRST_RUN_v0.4.2.md`.

Run from the F005 instance root: `run_all_v042.cmd`.

Key deliverables at run time:

- All v0.4.1-generated INPUT waveform candidates scored, without the 15,000-pair cap; no claim to exhaustive all-pairs or source-family identity.
- Source hashes compared to v0.3 and v0.4.1; TEST and OOD measured elevations never accessed.
- Conditional (known future acceleration) recursive ARX prediction: endpoint and full-path errors for 15 predeclared origin/horizon combinations.
- Persistence, linear, zero-response, and ARX-pole-derived unforced oscillator comparison.
- Validation group-robustness sensitivity for a heuristic input-screen-negative subset, not a certified group holdout.
- Auto-generated results JSON/CSV/Markdown/PDF.

Source dataset: Giulietti et al., *Robot-executed longitudinal sloshing dataset for rectangular tank liquid handling*, Zenodo v1.0.0, https://doi.org/10.5281/zenodo.20039757. Provider describes the first 5,000 as standard robotic motion laws and the final 4,822 as MSD-optimized motions; no source-defined waveform family identifier appears in the registered `trajectory_metadata.csv` schema.

This patch includes a copy of the v0.4.1 code in `tests/fixtures/` **solely for self-test portability**; runtime uses the installed, locked `data/f005_free_run_family_v0.4.1.py`.
