# Changelog

## 0.1.2 — Swirl-Clock phase-integrity / branch-continuation release

v0.1.2 is deliberately **not** a second confirmation attempt for the v0.1.1 phase target.  The v0.1.1 output audit showed that the packet **envelope return time** was reproducible, while the absolute carrier phase at that return was frequently under-resolved.  Because the measured observable itself changes in v0.1.2, the old `phi*=2.72 rad` target is retired from primary scoring and a new phase may only be *discovered* here.  A later independent release is required for confirmation.

### 1. Continuous packet-return refinement

**Changed:** the return envelope is first located on a coarse grid and then refined with bounded continuous optimization.  The optimizer tolerance is tied to

\[
|\omega|\,\Delta t \le 0.05\;\mathrm{rad}
\]

(or the stricter preset value).

**Why:** in v0.1.1 the typical phase advance between two global time samples was several radians for many `m=1` cases and still larger for `m=2`.  A 401-point grid could locate the slowly varying envelope but could not safely identify the carrier phase at its maximum.  Global oversampling by millions of points would be wasteful for very slow group-velocity branches, so v0.1.2 resolves the phase *locally around the continuously refined return maximum*.

### 2. Explicit numerical phase-uncertainty gate

**Changed:** every CLOSED case now reports

- `phase_sampling_step_rad`;
- `tau_return_numerical_uncertainty`;
- `dispersion_omega_rmse`;
- `phase_uncertainty_from_time_rad`;
- `phase_uncertainty_from_dispersion_rad`;
- `phase_uncertainty_rad`;
- `phase_gate_valid`.

The default phase gate requires `phase_uncertainty_rad <= 0.35 rad` and return coherence >= 0.50.  The dedicated stress preset tightens this to 0.20 rad.

**Why:** phase error accumulates over the loop.  A small local dispersion-frequency error \(\sigma_\omega\) produces approximately

\[
\delta\phi_{\rm disp}\simeq \sigma_\omega\tau_{\rm return}.
\]

This is especially severe for the slow branch, where \(\tau_{\rm return}\) can be orders of magnitude larger than for the fast branch.  Delay validity and phase validity are therefore separate gates: a case may measure a good return time but still be forbidden from phase-growth statistics.

### 3. Corrected Swirl-Clock cycle count

**Changed:** `carrier_phase_cycles_at_return` now records

\[
N_{\rm cyc}=\frac{|\Im\lambda|\tau_{\rm return}}{2\pi},
\]

instead of deriving a "cycle count" from the wrapped phase.

**Why:** a wrapped phase lies in one \(2\pi\) interval and cannot encode whether the mode completed 2, 200, or 2000 turns before returning.  The actual cycle count is required to understand phase sensitivity.

### 4. Intrinsic/co-moving eigenfrequency

**Changed:** each eigenmode now carries an energy-weighted advective frequency

\[
\omega_{\rm adv}=\langle mV_\theta/r+kU_s\rangle_E
\]

and

\[
\boxed{\omega_{\rm int}=\omega-\omega_{\rm adv}}.
\]

New outputs include `advective_frequency_mode_weighted`, `omega_intrinsic`, `T_intrinsic`, and `intrinsic_over_swirl_frequency_ratio`.

**Why:** v0.1.1 mixed lab-frame modal oscillation with Doppler/advection by the base axial/swirl flow.  A Swirl Clock comparison should expose both the laboratory frequency and the co-moving/internal frequency rather than silently identifying them.

### 5. Axial-flow eigenbranch continuation

**Changed:** v0.1.2 can start from a preregistered axial-flow anchor and continue the eigenvector to the requested `U_s/V_theta` using overlap at intermediate steps.  The history and minimum overlap are recorded.  The new clock-focused presets enable this; legacy broad presets keep it optional.

**Why:** the v0.1.1 audit found two sharply different `m=1` regimes.  Selecting the "worst admissible hybrid mode" independently at every axial-flow value can jump from one spectral branch to another.  Such branch switching can manufacture an apparent phase law.  Continuation asks whether the *same eigenmode family* evolves into the fast or slow regime.

### 6. Preregistered clock-regime split

v0.1.2 labels CLOSED modes before reveal as:

- `FAST_SWIRL_LOCKED` when
  \[
  0.60\le |\Im\lambda|/\Omega_{\rm swirl}\le1.40,
  \qquad |v_g|\ge0.05;
  \]
- `SLOW_MODE` when
  \[
  |\Im\lambda|/\Omega_{\rm swirl}\le0.20,
  \qquad |v_g|\le0.05;
  \]
- `OTHER_BRANCH` otherwise.

**Why:** v0.1.1 showed an approximately 1:1 swirl-locked branch for negative axial flow and a near-stationary slow branch for positive axial flow.  Pooling them into one circular regression violated the assumption of one common clock law.  The numeric boundaries are broad separators around the observed gap, not fitted stability thresholds.

### 7. Bounded growth response replaces singular log-ratio in phase fits and carrier votes

**Changed:** phase regressions and primary carrier-level closure votes use

\[
E_g=\frac{g_C-g_S}{|g_C|+|g_S|+2g_0},
\qquad -1<E_g<1,
\]

where negative means CLOSED has lower positive growth.  The old log ratio is retained only as a diagnostic/compatibility field and no longer determines the primary closure effect gate.

**Why:** a case with `g_C = 0` and a tiny positive control growth can produce a log ratio with magnitude >10 even though both rates are small.  Such a point has excessive regression leverage.  The bounded response preserves direction and relative scale without a singularity at neutral stability.

### 8. Old 2.72-rad confirmation target retired

**Changed:** the v0.1.1 `m=1` confirmatory and `m=2` target-control runners are removed from the primary release.  v0.1.2 instead provides:

- `run_all_swirl_clock_phase_discovery.cmd` — `m=1` discovery on the corrected phase observable;
- `run_all_swirl_clock_m2_diagnostic.cmd` — `m=2` diagnostic with no inherited phase target;
- `run_all_swirl_clock_branch_map.cmd` — dense axial-flow branch map;
- `run_all_phase_resolution_stress.cmd` — stricter radial/phase-resolution audit.

**Why:** after changing how phase is measured, recycling the old optimum would be pseudo-confirmation.  v0.1.2 is permitted to estimate a new `phase_min_rad`, but `PHASE_DISCOVERY.json` marks it `discovery_only=true`.  A later independent release must freeze that value before new data are run.

### 9. Discovery is carrier-clustered and regime-specific

**Changed:** phase discovery removes per-carrier growth baselines, fits circular `cos(phi), sin(phi)` structure only on phase-valid rows, performs leave-one-carrier-out CV, carrier-grouped phase permutation, and carrier bootstrap of the discovered phase.  The primary `m=1` discovery is restricted to `FAST_SWIRL_LOCKED`.

**Why:** geometry-specific growth offsets and repeated `(profile, axial ratio, n)` rows from the same carrier are not independent evidence.  The phase should survive carrier holdout rather than exploit within-carrier repetition.

### 10. No change to the core prohibition

Still forbidden in the physics/eigenmode path:

- `tau_delay`;
- `feedback_delay`;
- user-selected return time;
- target phase used by the eigenproblem/dynamics.

The delay, phase and any discovered optimum remain measured outputs only.

## 0.1.1

- Fixed carrier closure statistics to use only pairs where CLOSED and control modes are both converged/valid.
- Fixed delay aggregate to use only valid CLOSED modes with successful wave-packet return.
- Neutral/neutral growth became an explicit tie.
- Replaced one-sided non-integer closure control by symmetric `k0-dk` / `k0+dk` averaging.
- Exported first-generation Swirl-Clock variables.
- Ran the preregistered `m=1`, `phi*=2.72 rad` confirmation and matched `m=2` control.

## 0.1.0

- Initial standalone finite-core axial/toroidal eigenmode blind falsifier.
- Linearized incompressible Euler generalized eigenproblem for three smooth finite-core profiles.
- Closed carrier length + curvature validity + Bishop holonomy.
- Geometric closed-loop wavenumber versus blinded non-integer phase-closure null.
- Eigenbranch continuation in k, measured group velocity, periodic wave-packet return, and measured loop phase.
- No explicit feedback delay or target phase in dynamics.
