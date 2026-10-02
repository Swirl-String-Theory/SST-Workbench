# SC-II Intrinsic Modal Phase Swirl Clock — preregistered protocol v1.0

## Hypothesis

SC-II is intentionally distinct from the older SC-I recurrent-shape hypothesis.
SC-I asks whether the full vortex shape returns to (approximately) the same state.
SC-II does **not** require full-shape recurrence.

The SC-II hypothesis is that a vortex structure can carry an internally generated,
monotonically advancing modal phase

\[
\phi_{\rm sc}(t),\qquad \Omega_{\rm sc}=\dot\phi_{\rm sc},
\]

while the slow mean geometry and modal envelope may evolve.

Operational decomposition:

\[
X(s,t)=X_{\rm slow}(s,t)+A(t)\Phi(s,\phi_{\rm sc}(t))+\epsilon(s,t).
\]

The primary observable is the phase of a **frozen early-discovery POD coordinate**.
The mode is learned before the holdout is scored.

## Primary phase estimator

For each frozen modal coordinate `a_k(t)`:

1. remove a deterministic affine slow trend;
2. construct the analytic signal with a Hilbert transform;
3. unwrap and orient the phase so the net phase direction is positive;
4. score only the post-discovery holdout.

\[
z_k(t)=a_k^{\rm detrended}(t)+i\,\mathcal H[a_k^{\rm detrended}](t),
\qquad
\phi_k(t)=\operatorname{unwrap}\arg z_k(t).
\]

The primary candidate must be in the **natural** (`probe_arm=0`) channel.
The odd ±probe channel is retained only as a diagnostic/null and can never by
itself produce an SC-II PASS.

## BASIC preregistered gates

A provisional SC-II candidate requires all gates below, plus the unchanged
Stage-A numerical geometry gate.

- P1 intrinsic mode: discovery energy >= 0.03 and holdout amplitude >= 1e-5.
- P2 phase progression: >= 4 phase wraps and >= 0.90 positive phase increments.
- P3 frequency coherence: phase-linearity R² >= 0.90, cycle-period CV <= 0.15,
  spectral peak fraction >= 0.30, harmonic R² >= 0.50.
- P4 phase/envelope stability: one-cycle phase diffusion RMS <= 0.75 rad,
  envelope CV <= 0.60, end/start envelope ratio in [0.40, 2.50], and >= 0.95
  reliable-envelope samples.
- P5 out-of-sample predictability: a constant angular velocity fitted on the
  first 40% of the holdout predicts the remaining holdout with RMS phase error
  <= 1.00 rad and terminal phase error <= 1.57 rad.
- P6 natural channel: mandatory.

No threshold may be relaxed after inspecting a particular carrier.

## Numerical certification

The Stage-A geometry policy is inherited unchanged from the certified modal
workbench. BASIC requires full T=24 completion, `ds_cv <= 0.20`, and the
predeclared mesh/physical velocity gate.

A provisional SC-II phase candidate is replayed under low and high tangential
mesh-gauge settings. The phase clock must survive both replays, and the period
spread must remain <= 0.15. This tests that the clock is not merely a bead-
redistribution gauge artifact.

## Provenance robustness

Fremlin variants (for example `3_1`, `3_1p`, `3_1u`) are separate shape seeds
but one source-family vote. Gilbert, Katlas and KnotPlot are independent opaque
source families. Cross-source robustness requires at least two independent
families and a source-family candidate fraction >= 2/3 with period spread <= 0.30.

## Stage B causal mechanism

Stage B is separate from SC-II existence. For a mesh-gauge-certified phase
clock, the frozen Stage-A mode is projected into material-core and fixed-core
runs. The test asks whether local stretch predicts delayed modulation of
instantaneous phase velocity better than zero lag and phase-scrambled nulls,
and whether that coupling is stronger for material core than fixed core.

A Stage-A phase PASS can therefore coexist with a Stage-B mechanism FAIL.

## Interpretation

- `FAIL_SCII_NO_INTRINSIC_MODAL_PHASE_CLOCK`: enough valid coverage and no mode
  passes the preregistered phase gates.
- `INDETERMINATE_SCII_INSUFFICIENT_VALID_COVERAGE`: geometry coverage is too
  small for a global negative claim.
- `PASS_SCII_INTRINSIC_PHASE_CLOCK_MESH_GAUGE_CERTIFIED`: a phase clock exists
  in at least one carrier under the numerical model.
- `PASS_SCII_PROVENANCE_ROBUST_PHASE_CLOCK`: the phase clock survives across
  independent source families for the same topology.
- `PASS_SCII_CANDIDATE_PHASE_CLOCK_MECHANISM`: Stage B also supports the
  preregistered stretch/phase-modulation mechanism.

SC-II is a falsifiable successor hypothesis; it does not retroactively convert
SC-I full-shape-recurrence failures into passes.
