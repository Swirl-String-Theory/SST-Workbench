# Validation — v0.3.0 final packaging pass

Generation-time validation was rerun against the final strict-blind source tree and the bundled **SST Parametric Trefoil Seed Atlas v1.0.0 (PTSA)**.

## Static strict-blind audit

**PASS** — `violations = []` across the complete pre-reveal path, including seed qualification, inventory, dynamics, modal extraction, energy and blind analysis. No SST canonical numerical fingerprint, SI action target, Planck target, or reveal/provenance import was detected.

See `validation_reference/BLIND_CODE_AUDIT.json`.

## Python self-tests

```text
11 tests run
10 PASS
1 SKIP
```

The single SKIP is native C++/Python parity because this generation environment does not contain the built Windows/MSVC extension. **No native PASS is claimed here.** Production BASIC/EXTENDED/HIGHRES keeps `require_native=true`.

## PTSA integrity and BASIC-threshold Python replay

The self-contained atlas contains **48 analytic candidates**, each with 512 raw XYZ points. A pure-Python replay retained BASIC qualification resolution/time/thresholds while changing only `require_native=false` for generation-time validation:

```text
candidates = 48
eligible   = 48
selected   = 6
errors     = 0
rolling_coherence = 0.674959465291 ... 0.965413010292
shape_drift       = 0.047965493720 ... 0.061283033698
mesh_cv           = 0.080579333345 ... 0.140091973378
score             = 0.609273483934 ... 0.760749127893
```

This validates atlas parsing, dimensionless normalization, qualification ordering, public identity withholding and private selected-input generation. It is **not** a native physical result.

## Spectral window guard

`tests/test_v030_ptsa.py` verifies that an FFT maximum in the first non-zero frequency bin is marked `frequency_window_limited=true`. Production campaign logic can extend the dimensionless observation horizon before accepting recurrence/frequency gates. Temporal refinements then reuse a shared physical dimensionless horizon rather than independently choosing favorable windows.

## Synthetic dimensionless action controls

Positive pipeline control:

```text
blind_pass = True
median Jf_hat = 0.371956194259
CV = 0.0039693181
median amplitude log-slope = -0.000453576602
```

Classical-continuity negative control:

```text
blind_pass = False
classical continuity null triggered = True
median amplitude log-slope = 1.99943309
```

The controls are pipeline tests only. The positive control uses an arbitrary dimensionless constant; it is not SST/Planck evidence.

## Final raw-geometry fallback smoke test

One prequalified PTSA carrier was passed through pure-Python campaign → blind preparation → blind analysis. Execution errors were zero; the scientific verdict failed closed:

```text
blind_pass = False
UA2_recurrent_mode_prerequisite = FAIL
UA2c_positive_resolved_dimensionless_energy = FAIL
UA3b_temporal_convergence = SKIP_PREREQUISITE
UA4_reject_classical_continuous_action = SKIP_PREREQUISITE
UA5_dimensionless_action_amplitude_independence = SKIP_PREREQUISITE
UA6_dimensionless_action_universality = SKIP_PREREQUISITE
UA7_spatial_convergence = SKIP_PREREQUISITE
```

This confirms the v0.3.0 `SKIP_PREREQUISITE` semantics: unresolved recurrence/energy cannot be converted into a downstream action success.

## Output/archive convention

Production runners write to `./Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs/`. Blind completion creates both `../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs.zip` and `../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs_BLIND.zip`; both are blind-safe. Private reveal keys stay outside the output root. Explicit reveal creates `../Wien_Planck_SST_Field_Matter_Closure_Falsifier_v0.3.0-outputs_REVEALED.zip`.

## Scientific status

v0.3.0 is a **numerical centerline-model falsifier** with strict anti-circularity. PTSA is a search space, not a certified preferred particle geometry. A true SST claim still requires native Windows validation, stronger topology certification where needed, and ultimately finite-core/full-3D Euler closure beyond the regularized line-filament model.
