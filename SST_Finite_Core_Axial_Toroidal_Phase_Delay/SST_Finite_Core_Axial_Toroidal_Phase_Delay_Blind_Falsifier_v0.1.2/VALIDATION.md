# Validation — v0.1.2

Validation date: 2026-08-24.

## Release purpose

v0.1.2 changes the **phase observable and branch-tracking methodology** while keeping the finite-core local Euler model and C++ geometry helper architecture.  Therefore the principal validation question is not whether the previous `2.72 rad` result repeats; it is whether the new clock measurement can distinguish a valid delay from an invalid/uncertain absolute phase without using a free delay or target phase.

## Python regression suite

Final development run:

```text
23 passed
```

Covered regressions include:

- finite-core generalized eigenproblem;
- symmetric `k0-dk / k0+dk` control;
- blind -> seal -> reveal integrity;
- neutral-mode tie handling;
- bounded growth response;
- continuous wave-packet return refinement;
- adaptive local phase-step target;
- dispersion-uncertainty phase rejection;
- intrinsic/co-moving eigenfrequency identity;
- axial-flow eigenvector continuation;
- FAST/SLOW clock-regime classification;
- synthetic phase-discovery recovery without a preregistered target;
- prohibition of free delay/target-phase tokens in runtime physics modules.

`python -m compileall` also passed for `src/` and `tests/`.

## Configuration audit

All 10 JSON presets parse successfully.

Prepared blind campaign sizes:

```text
preset_basic.json                         8 pairs / 16 candidates
preset_chirality_sign.json              120 pairs / 240 candidates
preset_core_radius.json                  48 pairs / 96 candidates
preset_extended.json                     96 pairs / 192 candidates
preset_phase_resolution_stress.json      16 pairs / 32 candidates
preset_profile_robustness.json           72 pairs / 144 candidates
preset_radial_convergence.json           16 pairs / 32 candidates
preset_swirl_clock_branch_map.json       72 pairs / 144 candidates
preset_swirl_clock_m2_diagnostic.json    96 pairs / 192 candidates
preset_swirl_clock_phase_discovery.json  96 pairs / 192 candidates
```

The v0.1.1 `2.72 rad` confirmatory target presets are deliberately absent from v0.1.2 primary configuration because the phase observable changed.

## Native C++ audit

`cpp/native.cpp` SHA-256:

```text
9c0b0bee4dab1295d045fa8e2479c7e7b0199fc627c960509c50382fd1cf91c2
```

This is byte-identical to the native helper in v0.1.1, whose Windows/MSVC path was exercised by the prior campaign.  In the v0.1.2 artifact environment it was additionally compiled and loaded with:

```text
Python 3.13.5
G++ 14.2.0
C++17 + OpenMP
pybind11 headers from the installed PyTorch header set
backend = cpp-pybind11
```

Native geometry smoke on a 1000-point unit circle returned length `6.283174971759119`.

The temporary Linux `.so` used for this audit is removed before release packaging; Windows builds its own `.pyd` through `run_01_build_native.cmd`.

## Native blind -> seal -> reveal smoke

A reduced v0.1.2 `phase_discovery_m1` campaign was run with `require_native=true`, branch continuation enabled and two axial-flow points.

Observed:

```text
backend                                  cpp-pybind11
prepare format                           SST-FINITE-CORE-PREPARE-1.2
blind format                             SST-FINITE-CORE-BLIND-1.2
reveal format                            SST-FINITE-CORE-REVEAL-1.2
blind pairs                              2
finite-core mode valid fraction          1.0
self-generated delay gate                PASS
phase measurement valid fraction         1.0
verdict                                  M1_PHASE_DISCOVERY_INCOMPLETE
```

`M1_PHASE_DISCOVERY_INCOMPLETE` is the correct result for a two-pair smoke because the discovery carrier/sample thresholds were not met.  The smoke therefore demonstrates that the pipeline does not promote an undersized test into a positive phase claim.

Example certified clock diagnostics from this smoke included:

```text
phase_sampling_step_rad     0.05
phase_uncertainty_rad       ~3e-4 rad
carrier cycles at return    >100 cycles
clock regime                FAST_SWIRL_LOCKED
```

## Phase-integrity falsifier checks

### Linear-dispersion recovery

A synthetic exactly linear local dispersion relation recovers the predicted loop return within the regression tolerance and passes the `0.05 rad` local phase-step target.

### Delay-pass / phase-fail separation

The same synthetic packet with deliberately inflated measured dispersion-frequency uncertainty still recovers the group delay but fails `phase_valid` because

\[
\delta\phi_{disp}=\sigma_\omega\tau_{ret}
\]

exceeds the phase-uncertainty threshold.

This is an explicit test that v0.1.2 can say:

```text
DELAY VALID
PHASE INVALID
```

rather than allowing a good envelope return to certify an unresolved feedback phase.

## Runtime isolation audit

The runtime physics/blind modules `analyze.py`, `eigen.py`, `delay.py`, and `workflow.py` contain none of:

```text
confirmatory_phase_target
tau_delay
feedback_delay
user_delay
```

The discovered phase can only be computed during reveal after the blind result tree is sealed.

## Scientific limitations

v0.1.2 remains a **slender finite-core, locally columnar, linear incompressible-Euler mechanism falsifier**.  Knot geometry enters through loop length, curvature validity and Bishop holonomy; axial-flow continuation tracks the local spectral branch.  This is not yet a full curved-core 3-D Euler/Floquet solver and does not establish nonlinear orbital stability.

The `FAST_SWIRL_LOCKED` / `SLOW_MODE` boundaries are preregistered broad separators motivated by the v0.1.1 audit.  They are not fundamental constants and must be treated as classification gates to be challenged by later data.

Any `phase_min_rad` produced by v0.1.2 is **discovery only**.  Confirmation requires a later release that freezes the newly measured phase before independent carriers/data are run.

## Final source-only packaging audit

Before manifest/ZIP generation:

- temporary Linux native `.so` removed;
- no `.pyd`, `.so`, `.dll`, `.pyc`, `.venv`, `build/`, `outputs/` or Python cache directories included;
- `MANIFEST.sha256` verifies all 90 listed distribution files.

The external release ZIP is additionally tested with `unzip -t` and receives a separate SHA-256 file next to the archive.
