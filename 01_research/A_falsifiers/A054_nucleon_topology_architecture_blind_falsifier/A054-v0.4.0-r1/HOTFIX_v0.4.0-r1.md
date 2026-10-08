# A054 v0.4.0-r1 execution/profile hotfix

This maintenance release repairs pre-run execution/configuration defects in v0.4.0. No scientific campaign completed under the broken release.

## Fixes
1. `%~dp0` is canonicalized to a path without a trailing backslash before `pip install -e`.
2. Framework profile is `multilibrary_gpu`, a framework-owned profile; experiment-specific mechanism settings remain in the instance.
3. Every command stage propagates a non-zero exit code. The previous scripts could continue after pip failure and could finish with exit code 0 after a Python traceback.
4. `run_certify_selected.cmd` also uses a normalized instance root.

## Scientific invariants
Unchanged: source geometries and hashes, mechanism definitions, gain grid, v0.2 hard gates, blind/reveal mapping, gate DAG, source contract, science contract and C++ kernel.

The canonical SST Falsifier Framework v1.0.4 is not modified. A framework patch is neither required nor appropriate for this instance-specific profile name error.
