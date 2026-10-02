# A050 v0.3.0 preregistration — frozen before dynamics

## Status

Confirmatory external-geometry transfer test. The v0.2.2 result `MODAL_PERSISTENCE_NOT_REPRODUCED` and the v0.2.3 diagnostic `ISOLATED_M3_TRAJECTORY_BEHAVIOR` remain historical results and are not overwritten.

## Frozen source-selection rule

Primary external geometry: four deterministic quantile representatives from nonduplicate A001 upstream-reference carriers that pass the PKLSA v0.3.1 hard literature gates, plus the single A004 independent ideal-reference carrier. A003 QHP endpoints are diagnostic only. Source/provider identity is reveal-only during dynamics.

No synthetic fallback is allowed if any frozen primary raw source is absent or has a SHA-256 mismatch.

## Frozen dynamics/gates

- curve samples: 72;
- dimensionless core ratio: 0.1;
- time step: 0.02;
- modal horizon: 2048 steps;
- checkpoints: 320, 640, 1024, 1536, 2048;
- late checkpoints: 640, 1024, 1536, 2048;
- persistent carrier: >=3 qualified late checkpoints, qualified final checkpoint, frequency CV <=0.15;
- modal qualification thresholds inherited unchanged: dominant fraction >=0.24, phase R^2 >=0.55, phase advance >=0.10 cycles;
- five transverse holdouts per primary base, RMS 0.00125;
- robust base: baseline persistent and >=4/5 holdouts persistent on the same branch;
- anonymous source-group requirements: S01 >=2 robust bases; S02 >=1 robust base;
- no hard target mode number;
- temporal-memory horizon: 1024 steps, nested windows 80/160/320/640/1024;
- memory present on >=3/5 primary bases; converged on >=2/5;
- numerical modal convergence, if source transfer succeeds: N={56,72,96}, dt={0.02,0.01}, same end time, relative frequency span <=0.15;
- Floquet/RPO inactive.

The exact source panel, raw hashes, analysis code and configuration are cryptographically sealed in `config/SEAL_v0.3.0.json`.
