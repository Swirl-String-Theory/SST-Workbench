# A058-v0.3.1 — local validation, 21 October 2026

## Verified defect

- The source `.sst_framework_root` contains `../../../../06_templates/SST_Falsifier_Framework/SST_Falsifier_Framework_v1.0.8`.
- In the original source location it points to the Workbench template tree. In the deeper v0.3.0 cloned tree it points elsewhere.
- The original `framework_bootstrap.py` explicitly prioritizes `SST_FALSIFIER_FRAMEWORK_ROOT` over the relative locator. The v0.3.1 coordinator supplies a SHA-verified original source-relative absolute v1.0.8 root in that variable.
- No frozen file mutation is required. Regression test constructs both directory layouts and confirms the old locator fails in the clone and the pinned correction resolves.

## Checks

- `python bridge.py SELFTEST`: PASS, synthetic contract only.
- `python -m unittest discover -s tests -v`: 10/10 PASS.
- `python bridge.py DIAGNOSE`: PASS on no-workspace branch; correctly returns `MISSING_CLONE_MANIFEST` and no false root-cause claim when no legacy workspace is attached.
- `python bridge.py AUDIT_CONTROLS`: PASS; emits screenshot-derived controls and mode restrictions without writing frozen data.
- Standalone command-probe script generation: PASS; 5 distinct `kpc` scripts, manifest hashes, no execution claimed.
- Independent segment-distance unit tests: crossed segments detected, separated square not flagged, parallel segments metric validated.
- Python syntax check: PASS.
- Native Windows/KnotPlot/framework acceptance: **NOT RUN**.
- Failed original FREEZE/BASIC/2048/FULL retest: **NOT RUN**.
- Physical/convergence/collision certification: **NOT ESTABLISHED**.

## Gate preservation

A058-v0.2.9 existing source, anonymous axis map, v0.2.10 prior native results, blind private commitments and old G0–G9 are preserved. v0.3.1 is **a coordinator** and must not publish a `G1/G2/G8 PASS` merely because the process or its source code tests PASS.
