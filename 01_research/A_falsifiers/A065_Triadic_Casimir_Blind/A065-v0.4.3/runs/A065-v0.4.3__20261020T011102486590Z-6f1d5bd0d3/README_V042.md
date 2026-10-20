# A065-v0.4.2 — targeted Windows A003/GPU runtime correction

**Scope: software correction only.** A065 v0.4.1 is kept unchanged alongside this
release. It uses framework v1.0.10 CANONICAL_FROZEN and A003 v0.2.3.

## Fixed

- In `triadic/volume_v040.py`, `_screen_geometry` receives `{'source_resolution': c['source_resolution']}`. Previously it received an `int` and crashed with `TypeError: 'int' object is not subscriptable` when the authentic A003 atlas was present.
- `test_missing_A003_never_faked` now forces the absence of A003 via a mock and verifies `A003_ADAPTER_MISSING` without accessing the real atlas. New unit test verifies the correct dictionary adapter handoff.
- Isolated legacy framework-failure injection test mocks **only** the expensive additional science lanes to test the intended exitcode 3 and PDF behavior. This does NOT mock scientific runs or their outcomes in production.
- `run_all.cmd` uses the same **activated venv** when a local `.venv` does not exist. Added `check_arc_env.cmd` to report the selected Python and GPU packages.
- New run IDs, output directories, and framework instance use v0.4.2. The science contracts `VOLUME_EULER_V040.json` and `ARC_GPU_V041.json`, their original SHA-256 pins, gate definitions, A003 source hashes and all historic data/seals remain byte-for-byte unchanged.

## Correct GPU environment setup, Windows CMD

```cmd
cd /d C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A065_Triadic_Casimir_Blind\A065-v0.4.2
py -0p
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements_arc_v041.txt
check_arc_env.cmd
run_all.cmd VERIFY
run_all.cmd SELFTEST
run_all.cmd GPU_SMOKE
run_all.cmd GPU_CAMPAIGN
run_all.cmd ALL
```

If Python 3.12 is unavailable, use a supported installed Python whose Intel
`dpnp` and `dpctl` distributions provide compatible wheels. Do not install
into the frozen framework v1.0.10 environment. Use the configured
`SST_FALSIFIER_FRAMEWORK_ROOT`, `SST_A003_ADAPTER_ROOT` and `SST_ATLAS_ROOT`
from the prior run.

## Status boundaries

`GPU_SMOKE` and `GPU_CAMPAIGN` require a *real* Arc A770 Level Zero GPU. No
claim of GPU parity is made until the user executes them. The v0.4.1 Gaussian
initial-condition, numerical Euler approach, frozen gates G0-G48, physics
qualification and negative evidence remain unchanged.

The original `SOURCE_MANIFEST_V041.json` remains a historical v0.4.1 record;
`SOURCE_MANIFEST_V042.json` is the manifest for this release. An old
v0.4.1 framework FREEZE must **not** be reused for v0.4.2.
