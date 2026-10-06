# Validation report — 3_Maxwell_SST_Physical_Lines_Falsifier_v0.3.0

Artifact validation completed before packaging.

## Upstream integration

- Google Drive SST-Workbench E010 family inspected directly.
- Current design target found: `E010-v0.3.1`.
- Runtime resolver accepts `E010-v0.3.x` and chooses the newest semantic version unless pinned.
- Live E010 carrier envelopes, qualification metrics, independence ledger, raw hashes and geometry hashes are re-verified at runtime.
- The inspected E010 release is **not** globally promoted: its aggregate `full_campaign_gate_pass` / `publication_ready_geometry_layer` are recorded separately from carrier-level admission.

## Numerical/software checks

- Python compilation: PASS.
- Pure-Python tests: **6 passed**.
- Exact polygonal Hopf linking reference: PASS.
- Independent Biot--Savart circulation vs linking: PASS.
- Mutual helicity vs pairwise linking: PASS.
- Synthetic E010 source-native carrier loading + raw SHA + geometry SHA: PASS.
- Synthetic full `basic` blind campaign: PASS.
- Frozen-output verification: PASS.
- Unblind commitment verification: PASS.

Synthetic M6 software-reference result:

- `|Q|` for a Hopf-linked unit-circulation reference: approximately `1.0001`;
- fitted M6 slope in the end-to-end fixture: approximately `1.00005`;
- null-loop circulation: numerically consistent with zero;
- these are implementation checks, not physical SST evidence.

## C++ status in artifact runtime

The hosted build environment did not contain pybind11 headers, so the included C++ extensions were not compiled here. `run_00_install.cmd` installs pybind11, installs/builds the local E010-v0.3.x release into the same venv, builds the independent Maxwell-3 C++17/OpenMP extension, and runs its native self-test before the extended campaign.


## 2026-09-29 build hotfix

The Windows linker failure reported for the deeply nested A012 path was traced to an absolute C++ source path being replicated under setuptools `build\temp`, producing a 275-character `.exp` path. The build helper now uses `cpp/native.cpp` relative to the release root and short `build\t` / `build\l` directories. Pure-Python regression after this change: **6/6 PASS**. Windows/MSVC rebuild is pending execution on the Workbench host. No scientific logic changed.

## buildfix3 — repeated BASIC -> EXTENDED orchestration

The user Windows log showed that E010 C++ compilation and linking both succeeded, then the second
editable installation failed only while replacing an already-installed
`pklsa_builder\\_native.cp314-win_amd64.pyd` (`Access is denied`).  This is a repeat-install DLL
lock, not a compiler/linker or scientific failure.

Hotfix3 adds a fail-closed installation probe.  If the selected E010 release, distribution version,
and native module all match and the native binary is not older than its C++ source, the install
stage is reused.  Otherwise the original editable/native rebuild path remains mandatory.  No
scientific code or preregistration changed.
