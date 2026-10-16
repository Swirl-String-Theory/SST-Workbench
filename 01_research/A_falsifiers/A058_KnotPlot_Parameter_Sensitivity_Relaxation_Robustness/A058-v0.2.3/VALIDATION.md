# A058 v0.2.3 validation

Validation date: 2026-10-13.

## Target framework

- Pinned framework: `SST_Falsifier_Framework_v1.0.8`.
- Framework release metadata from the user's Google Drive identifies v1.0.8 as `LOCAL_VALIDATED_CANDIDATE`, based on v1.0.7 `CANONICAL_FROZEN`.
- v1.0.8 reports unchanged scientific gate semantics, numerical thresholds, C++/SYCL kernels, frozen protocol contents and source admissibility; its maintenance changes concern run IDs, locking and non-overwriting output/PDF/ZIP retention.
- A058 v0.2.3 is a new instance version; historical A058 versions remain pinned to their original frameworks.

## v0.2.2 defect addressed

The user-machine v0.2.2 install test completed Python/C++ setup and 12 package tests, then failed closed because one GUI slider was not present in the bare `reset all` parameter dump. v0.2.3 no longer assumes all sliders are globally visible. It records one provenance-only reset dump, then enables each anonymous GUI sector separately and reads the defaults exposed in that sector context.

## Added experimental lane

The design now contains eight anonymous sliders across six anonymous sectors. The new velocity-dependent lane has its exact GUI command mapping only in the private reveal domain. Its runtime provenance records the KnotPlot notice that Undamped dynamics is intended for that force. The scientific campaign nevertheless keeps the user-requested common Damped + No-Collide regime, so this lane is explicitly interpreted as a Damped compatibility/response test.

## Static/package tests

- Instance pytest: **16 passed** against an exact local mirror of the v1.0.8 framework modules retrieved from the user's Drive.
- Python source parsing/compilation: PASS.
- Campaign formula: `6 + 8 × 33 = 270` conditions.
- Synthetic campaign generation: **270 conditions**, 6 references, 8 axes.
- Synthetic analysis: **270/270** final coordinate sets consumed; **264** perturbation responses; special anonymous diagnostics S5/S6/S7 present.
- Exact-zero endpoints remain outside logarithmic/quadratic fits.
- Install contract statically enforces exactly one trefoil export and only a one-step dynamics-liveness check; no fixed long `ago` schedule is present.
- Scientific acquisition remains adaptive via small `go 32` observation windows.

## Framework-v1.0.8 contract simulation

Using the exact v1.0.8 science/source/gate/report/blind/protocol modules retrieved from the user's Drive on an isolated copy:

- science contract errors: `[]`
- source contract errors: `[]`
- gate plan errors: `[]`
- report contract errors: `[]`
- forbidden-term blind scan hits: `[]`
- nonced blind/reveal commitments: PASS
- protocol FREEZE: PASS
- frozen-protocol verify: PASS

Final isolated v1.0.8 FREEZE-simulation protocol bundle SHA-256: `daa9afe7a57239d76b9043178299f958f3ecfb09c7bbbe691b8b0f1b7bd2b4be`. The release itself does not ship a frozen protocol; the user's local FREEZE creates the authoritative preregistration artifact and should reproduce this bundle hash if the protocol bytes remain unchanged.

## Report

`report/FALSIFIER_REPORT.tex` compiles successfully with local `latexmk/pdflatex`.

## Native backend

The C++/pybind11 metric kernel is unchanged from the immediately preceding A058 package. A native compiler/pybind11 toolchain is not installed in this build sandbox, so no new local native binary is shipped. The user's v0.2.2 log demonstrates the same kernel class building successfully with MSVC 14.44, Python 3.14 and pybind11 3.1.0. `run_install.cmd` rebuilds it locally and fails closed on compiler failure.

## Required target-machine checks

The sandbox cannot execute the user's KnotPlot GUI/Windows executable. The authoritative target run must therefore still verify:

1. all six sector-enable commands are accepted;
2. all eight sliders appear in their enabled sector context;
3. each setter reproduces `1.25 ×` its measured sector-context default;
4. the trefoil is safe in Damped + No-Collide without geometric preconditioning;
5. `go 1` advances dynamics;
6. exactly one install-test trefoil ASCII export is produced;
7. the 270-condition adaptive campaign completes or records fail-closed diagnostics per condition.

If any of those checks fails, the campaign must not be interpreted as a slider-response result.
