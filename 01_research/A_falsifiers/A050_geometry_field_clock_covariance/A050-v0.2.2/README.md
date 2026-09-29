# A050-v0.2.2 — Long-Horizon Modal Persistence + Temporal-Memory Convergence Gate

Confirmatory successor to A050-v0.2.1. The package keeps the v0.2.0 legacy gates frozen, extends the pressure-field memory trajectory to 1024 steps, and moves the primary modal claim onto 20 pre-generated blinded holdout carriers observed for 2048 steps.

## Primary confirmatory structure

- 4 anonymous holdout groups × 5 independent small transverse perturbations = 20 carriers.
- Modal checkpoints: 320, 640, 1024, 1536, 2048.
- Persistent carrier: same qualifying branch at >=3/4 late checkpoints, final checkpoint qualified, frequency CV <=0.15.
- Confirmed anonymous group: >=4/5 carriers support the same persistent branch.
- Numerical modal convergence: N=56/72/96 plus dt=0.02/0.01 at equal end time, frequency span <=0.15.
- Temporal-memory windows: 80/160/320/640/1024, with legacy shuffled-null reproduction plus IPS/blocked-bootstrap convergence.
- Floquet/RPO search: intentionally inactive in v0.2.2.

## Build / test

```bat
run_setup.cmd
run_selftest.cmd
```

## Full blind campaign

```bat
run_all.cmd
```

This is intentionally much heavier than v0.2.1: it contains 20 × 2048-step holdout trajectories plus the 1024-step pressure-memory channel and conditional numerical convergence runs.

## Separation

`data/holdouts_blind/` contains only neutral carrier files. `data/HOLDOUT_MANIFEST.json` contains blind IDs, anonymous groups, and hashes. Geometry identity and perturbation provenance live only in `reveal/HOLDOUT_MAPPING_v0.2.2.json` and are not read by the blind executable.

See `PREREGISTRATION.md` and `config/frozen_preregistration_v0.2.2.json` for the frozen protocol.
