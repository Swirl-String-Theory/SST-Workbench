# Changelog

## v0.4.1 — 2026-09-21 (PC01)

- Production-certification regression pack (no new physics).
- Adds `pc01_regressions.py` Tests A/B/C:
  - parity-perfect + CFL-invalid → mirror PASS / physical INVALID_NUMERICS / no promotion
  - SELFTEST PASS-looking → promotion REJECT
  - weak manifold `f_proj=0.002` → `REDUCED_MANIFOLD_BREAKDOWN` / no auto-promote
- Wired into `run_all.cmd` before synthetic demo/audit.
- Depends on shared `SST-SCIENTIFIC-CERTIFICATE-1.0` / `promotable()` (PC00).
