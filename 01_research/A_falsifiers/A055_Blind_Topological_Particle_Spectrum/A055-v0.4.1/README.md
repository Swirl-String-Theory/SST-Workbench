# A055 v0.4.1 — Chiral Covariance and Directional-Bias Certification

Status: **FROZEN protocol package** on **SST Falsifier Framework v1.0.6**.

This version preserves the v0.4.0 equations, thresholds, source campaign, resolution ladder and Jacobian finite-difference controls. It changes execution/provenance behavior only:

- exact v1.0.6 framework pin via `.sst_framework_root`;
- frozen instance implementation commitment covering runtime Python/C++ and numerical config files, verified at G0;
- A054 isolated runner is reconstructed into a temporary import mirror from **only** `RUNNER_MANIFEST.json` entries;
- every staged runner file must match its registered SHA-256;
- unlisted `.pyd`/`.so`/`.dll` files are excluded, preventing ABI-tagged extension precedence from changing the imported implementation;
- if a manifest-listed native file is unavailable or altered, only an exact-SHA copy of the recorded upstream native source can restore it;
- G5 local C++ FP64 parity runs independently of G2;
- G8 requires valid G2 and G5 but does not require G3 PASS, so a clean absence of the fine signal can progress to a formal recurrence FAIL;
- diagnostic-only values are stored separately and cannot close blocked gates;
- reveal requires a terminal G8 and the v1.0.6 integrity/commitment checks.

## Canonical placement

```text
01_research/A_falsifiers/A055_Blind_Topological_Particle_Spectrum/A055-v0.4.1
```

Framework:

```text
06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.6
```

## Run

```bat
run_blind_only.cmd FULL C:\workspace\projects\SST-Workbench
```

Or, after installation:

```bat
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
run_reveal_if_allowed.cmd C:\workspace\projects\SST-Workbench
```

`run_blind_only.cmd` performs install, instance tests, framework selftest, idempotent FREEZE verification and the requested blind mode. It never executes reveal.
