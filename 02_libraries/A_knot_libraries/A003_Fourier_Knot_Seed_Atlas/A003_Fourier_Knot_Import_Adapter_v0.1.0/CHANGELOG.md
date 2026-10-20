# Changelog

## v0.1.0 — 2026-10-19

- New read-only external registry for 30 analytic seeds and BASIC/FULL (1200/2400/4800/9600).
- Pin atlas v0.1.1 manifest SHA-256; validate 240 XYZ sha256 hashes, identity mapping, cyclic geometry, and sampling correspondence.
- Representative projection mirror regression for all 30 seeds, explicitly **not** chirality certification.
- Preserve 20 measured arclength chord-quality warnings instead of silently smoothing or changing source bytes.
- Optional Knot Library v0.2.5 `load_geometry()` -> `prepare_for_falsifier()` conversion with library-version guard and explicit dimensional scale.
- Prevent topology from being promoted to `CERTIFIED` by analytic formula, file name, or KAtlas label.
- CLI and Windows `run_all.cmd`, 10 regression tests, portable sidecar registry and numerical audit.
- Known limitation: real v0.2.5 runtime `prepare` not executed here (contract-only stub regression). Later Knot Library releases not automatically compatible.
