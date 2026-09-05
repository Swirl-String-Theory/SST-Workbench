# Validation — v0.3.1

Generation-time validation was rerun after the v0.3.1 scientific-certification changes. Production BASIC/EXTENDED/HIGHRES still require the Windows native C++17/pybind11 backend; this environment does not provide that Windows/MSVC build, so **no native PASS is claimed here**.

## Static strict-blind audit

**PASS** — `validation_reference/BLIND_CODE_AUDIT.json` reports

```text
violations = []
pass       = true
```

The audited pre-reveal path includes campaign, energy, action preparation/scoring, dynamics, modal extraction, perturbation/mode projection, geometry, relative equilibrium, seed qualification, and inventory.

## Python self-tests

```text
15 tests run
14 PASS
1 SKIP
```

The single SKIP is the native C++/Python parity test because the native extension is not built in this generation environment.

New v0.3.1 unit coverage includes:

- iterative frequency-horizon extension over multiple rounds;
- normal-bundle projection of a mixed tangential/normal mode;
- gauge test showing a non-rigid tangential marker velocity can strongly affect the full residual while leaving the normal relative-equilibrium residual near zero;
- adaptive reparameterization activation on an intentionally bad marker mesh.

## PTSA BASIC-threshold Python qualification replay

A pure-Python replay changed only `require_native=false` for validation. It processed the self-contained PTSA v1.0.0:

```text
candidate_count = 48
eligible_count  = 48
selected_count  = 6
errors          = 0
```

Observed rolling coherence:

```text
min    = 0.674959465291
median = 0.834399623197
max    = 0.965413010292
```

With the v0.3.1 adaptive mesh trigger, maximum pre-cleanup qualification mesh CV was tightly bounded in this replay:

```text
min    = 0.101312150726
median = 0.103556575861
max    = 0.105774736140
```

This validates PTSA parsing, target-free qualification, adaptive mesh control, randomized public qualification output, and private selected-input generation. It is not a production physics result.

## Synthetic blind action controls

Positive dimensionless pipeline control:

```text
blind_pass = True
all v0.3.1 gates = PASS
median amplitude log-slope = -0.000453576602
```

Classical continuous-action negative control:

```text
blind_pass = False
UA4_reject_classical_continuous_action = FAIL
UA5_dimensionless_action_amplitude_independence = FAIL
median amplitude log-slope = 1.99943308747
```

The positive control uses an arbitrary dimensionless constant and is only a pipeline test.

## Raw PTSA fallback smoke test

A deliberately small pure-Python PTSA campaign was executed end-to-end using `config/fallback_validation.json`:

```text
expected_observations = 6
observations          = 6
ok_observations       = 6
error_observations    = 0
coverage_complete     = true
```

The blind result failed closed because the short validation horizon did not resolve recurrence and the matched mode-energy response was not positive:

```text
UA0_no_SST_SI_target_leak                  PASS
UA0b_complete_campaign_coverage             PASS
UA1_omega_equals_2pi_f                      PASS
UA2_recurrent_mode_prerequisite             FAIL
UA2a_frozen_mode_normal_content             PASS
UA2b_normal_relative_equilibrium            PASS
UA2c_positive_resolved_dimensionless_mode_energy FAIL
UA2d_matched_mode_energy_frequency          PASS
UA3_adaptive_mesh_quality                   PASS
UA3b_temporal_convergence                   SKIP_PREREQUISITE
UA4..UA7 action/convergence gates           SKIP_PREREQUISITE
```

This validates the new complete-coverage semantics and mode-matched pipeline without converting unresolved dynamics into a downstream action claim.

In the smoke run, the normal relative-equilibrium residuals were substantially smaller than the separately retained full-marker residuals, consistent with the intended gauge separation. This is a diagnostic validation, not a scientific PTSA result.

## Iterative horizon behavior

The unit test explicitly forces two consecutive window-limited rounds followed by a resolved spectrum. The certification routine performs three evaluations, records two extension rounds, and returns `RESOLVED`. A production run that remains unresolved at the configured factor/round cap returns `UNRESOLVED_HORIZON_CAP`.

## Matched frozen-mode action architecture

The v0.3.1 campaign has a dedicated discovery branch:

```text
broadband probe -> POD -> normal projection -> frozen mode
```

All action amplitudes then use

```text
X0 +/- A * frozen_mode
```

for both the line-energy difference and the dynamic frequency measurement. Each raw row carries

```text
matched_energy_frequency_same_frozen_mode = true
```

and the blind scorer has an explicit `UA2d` gate.

## Output/archive convention

Production runners write to:

```text
./Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs/
```

Blind completion creates:

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs.zip
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs_BLIND.zip
```

Private reveal keys remain outside the output root and are excluded from blind archives. Explicit reveal creates:

```text
../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.1-outputs_REVEALED.zip
```

## Scientific status

v0.3.1 is a strict-blind **regularized centerline numerical falsifier**. It does not certify full three-dimensional finite-core Euler stability, topology independently of source construction, or absolute action quantization. The main production test remains the native Windows PTSA run.
