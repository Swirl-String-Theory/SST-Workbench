# A048 v0.2.0 — authenticated geometry and independent Euler producer probe

**Executed: 45/45 tests PASS. Physical branch verdict: INDETERMINATE.**

All 48 geometries from the authentic PTSA v1 upstream archive were ingested, including archive and all candidate SHA-256 checks. Exactly one geometry was evolved with independent periodic incompressible Euler dynamics, separately for baseline and transverse centerline seed displacement. The exact older PKLSA `(48,1,512,3)` NPZ is still missing and its expected hash gate remains INDETERMINATE; the PTSA route is explicit and never impersonates it.

Build: `python setup.py build_ext --inplace`. Run: `python run_euler_smoke.py PATH_TO_SST_Parametric_Trefoil_Seed_Atlas_v1.0.0.zip`. `run_pipeline.py` still runs synthetic instrument qualification only. Packages are explicit in setup.py; no setuptools autodiscovery.

The short Euler probe ran dt, dt/2 and dt/4 to the same end time 0.048. Final-field differences reduced from 8.063e-9 to 5.038e-10; this qualifies a fixed-grid integrator, not physical branch convergence. Maximum relative energy drift was 8.098e-12, divergence RMS 1.214e-16, and Python/native seed relative discrepancy 1.049e-15.

The localized core fails admission: 1.604 cells/sigma versus minimum 4; 3*sigma*max(curvature)=2.105 versus maximum 0.5. Simultaneous curvature/sampling screens alone estimate N>=252, before nonlocal tube separation, periodic-box effects and convergence. This is a conservative grid estimate, not a validated production resolution or cost forecast.

Measured quantities are fixed Eulerian velocity probes, volume response, energy, helicity and divergence. No evolved centerline, material phase, circulation or topology is claimed to be measured. Spectral diagnostic code and averaged coherence controls exist; the short transient spectrum is not promoted to an eigenfrequency. Physical H0 versus H1 is NOT-IMPLEMENTED and its admission returns AMBIGUOUS.

See GATE_STATUS_MATRIX.json for all 74 backlog items and docs/CYCLE_EVALUATION.md for the next step. Every run and its BLIND/REVEALED/full ZIPs have unique falsifier/version/suite/UTC/ID names and SHA-256 sidecars. Prior runs are never overwritten.
