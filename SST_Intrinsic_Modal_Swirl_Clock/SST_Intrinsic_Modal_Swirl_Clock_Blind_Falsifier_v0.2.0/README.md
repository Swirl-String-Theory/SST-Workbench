# SST Intrinsic Modal Swirl-Clock Blind Falsifier v0.2.0

**Long-Horizon Mesh-Stabilized Recurrence Gate**

This release tests a narrower and stronger question than v0.1.x:

\[
\boxed{\text{Does a relaxed vortex carrier possess a genuinely recurrent intrinsic shape mode?}}
\]

Only if that question passes does the package ask whether material vortex stretching and a measured delay are a specific causal mechanism for that recurrence.

The default seed source is unchanged:

```text
..\..\KnotPlot\knots\final
```

No new KnotPlot seeds are required for this discovery release. The purpose is to observe free dynamics around the already Ridgerunner/KnotPlot-relaxed representatives.

---

## Why v0.2.0 was necessary

The v0.1.1 long-horizon BASIC campaign extended the observation to `T=12`, but almost every non-trivial carrier left the bead-spacing quality region before the end. The dominant numerical limitation therefore changed from **too little time** to **Lagrangian mesh degradation**.

Simply increasing `T` again would not be a valid test.

v0.2.0 separates the problem into two stages.

```text
relaxed centerline
      |
      v
blind -eps / 0 / +eps trajectories
      |
      v
STAGE A: geometry-only, tangentially mesh-stabilized long run
      |
      +--> natural carrier-motion POD
      +--> odd linear-response POD
      |
      v
multi-cycle + multi-return recurrence gates
      |
      +-- FAIL --> no Stage-B mechanism claim
      |
      v
STAGE B: material-labelled short causal test
      |
      +--> material-core
      +--> fixed-core null
      |
      v
stretch -> measured delay -> modal acceleration
```

---

# 1. Stage A: recurrence before mechanism

Stage A is deliberately **geometry-only**. It asks whether the centerline shape has a recurrent collective orbit before trying to explain why.

## 1.1 Three matched arms

Every carrier now has:

\[
-\epsilon,\qquad 0,\qquad +\epsilon.
\]

The zero arm is new in v0.2.0.

This gives two independent observables.

### Natural-motion channel

The unperturbed carrier itself:

\[
\delta\mathbf X_{\rm natural}(s,t)
=
\mathbf X_0(s,t)-\mathbf X_0(s,0),
\]

after rigid alignment and normal projection.

This channel can see a collective collapse/reversal shared by both perturbation arms; v0.1.x could subtract such motion away.

### Odd linear-response channel

\[
\delta\mathbf X_{\rm odd}(s,t)
=
\frac{\mathbf X_+(s,t)-\mathbf X_-(s,t)}{2\epsilon}.
\]

This isolates the first-order response around the carrier.

The even probe contamination is also measured:

\[
\delta\mathbf X_{\rm even}
=
\frac{\mathbf X_++\mathbf X_-}{2}-\mathbf X_0.
\]

A large even contribution invalidates a supposedly linear odd-response candidate.

---

# 2. Fixed absolute discovery window

v0.1.1 used a discovery **fraction**. Increasing total runtime therefore also changed the learned POD basis.

v0.2.0 instead freezes:

```text
discovery_time = 1.2
```

independent of the total horizon.

The early shape response is decomposed by POD/SVD:

\[
\delta\mathbf X_\perp(s,t)
=
\sum_k a_k(t)\,\boldsymbol\phi_k(s).
\]

The spatial modes \(\boldsymbol\phi_k\) are learned only before `t=1.2`, then frozen. The long holdout is projected onto those same modes.

Thus a longer run no longer silently redefines what the candidate mode is.

---

# 3. Tangential mesh stabilization

Stage A adds a numerical redistribution velocity

\[
\mathbf u_{\rm mesh}=\lambda\,
\bigl[(\mathbf X_{\rm uniform}-\mathbf X)\cdot\hat{\mathbf t}\bigr]\hat{\mathbf t}.
\]

Only its **tangential projection** is retained.

Therefore no explicit normal restoring force is inserted into the continuum shape dynamics. The purpose is solely to prevent beads from clustering while the normal Biot-Savart dynamics evolves the curve.

The default redistribution rate is `4.0` in nondimensional inverse-time units; it is numerical, not a physical SST parameter.

The package reports:

```text
max_ds_cv
mesh_speed_rms
physical_speed_rms
max_mesh_to_physical_rms_ratio
stop_reason
```

and still contains a hard Stage-A mesh-quality stop.

### Important interpretation rule

Stage A does **not** interpret bead indices as material labels. A sliding tangential numerical mesh cannot simultaneously be treated as Lagrangian material parcels.

For that reason Stage A must not be used to claim local stretch/core causality.

---

# 4. Stage-A finite-core law

The default geometry-only core branch is:

\[
a^2(t)L(t)=a_0^2L_0,
\]

with a **uniform** core radius around the curve.

This preserves a global tube-volume-like quantity while remaining compatible with a sliding numerical parametrization.

It is not the local material law

\[
a_i^2\ell_i=\text{const}.
\]

That local law is reserved for Stage B.

---

# 5. Strong recurrence gates

A sinusoidal-looking Fourier peak is not sufficient.

For each frozen mode, v0.2.0 estimates \(T_k\) and evaluates the phase-space state

\[
\mathbf z_k=(a_k,\dot a_k).
\]

It then measures closure at multiple returns:

\[
E_n=
D\!\left(\mathbf z_k(t+nT_k),\mathbf z_k(t)\right),
\qquad n=1,2,3,4.
\]

A Stage-A candidate must satisfy all of the following classes of gates:

1. **SA1 intrinsic mode** — sufficient POD energy and holdout amplitude.
2. **SA2 multi-cycle** — BASIC requires at least 4 holdout cycles; EXTENDED at least 6.
3. **SA3 multi-return closure** — several independent returns must close in phase space.
4. **SA4 stationarity** — cycle period, amplitude, and cycle mean must remain sufficiently stationary.
5. **Geometry quality** — full requested Stage-A horizon must be completed below the mesh gate.
6. **Odd-channel linearity** — even probe contamination must remain bounded.

Typical BASIC thresholds include:

```text
cycles >= 4
median multi-return closure <= 0.45
max multi-return closure <= 0.80
period CV <= 0.15
amplitude CV <= 0.25
cycle-mean drift / amplitude <= 0.35
```

EXTENDED is stricter.

---

# 6. Stage B: causal mechanism only after Stage A

Stage B runs only carriers that produced at least one Stage-A recurrence candidate.

This can reduce the expensive material-labelled campaign from dozens of carriers to only the scientifically relevant subset.

Stage B uses:

### Material core

\[
a_i^2(t)\ell_i(t)=a_{i0}^2\ell_{i0}
\]

versus

### Fixed core

\[
a_i(t)=a_0.
\]

There is **no tangential remeshing** in Stage B, because the segment identities now carry material meaning.

The Stage-A spatial mode is frozen and reused. Stage B cannot learn a more favorable mode.

The causal chain tested is:

\[
a_k
\rightarrow
\sigma_k
\rightarrow
\tau_k^{\rm measured}
\rightarrow
\ddot a_k(t+\tau_k).
\]

The delay is selected in the Stage-B discovery interval only and then tested unchanged in holdout. Phase/circular scrambling and zero-lag comparisons remain null tests.

A full mechanism candidate requires material-core delayed coupling to outperform the fixed-core control.

---

# 7. Verdict hierarchy

The final blind verdict intentionally separates existence from mechanism.

### No recurrent clock

```text
FAIL_STAGE_A_NO_RECURRENT_SHAPE_CLOCK
```

No frozen intrinsic mode survives the long multi-return recurrence gates.

### Recurrent shape mode, mechanism not established

```text
PASS_STAGE_A_RECURRENCE__FAIL_OR_INDETERMINATE_STAGE_B_CAUSALITY
```

A genuine recurrent collective mode exists, but the proposed local stretch/delay/material-core mechanism is not established.

### Candidate swirl-clock mechanism

```text
PASS_CANDIDATE_INTRINSIC_SWIRL_CLOCK_MECHANISM
```

This is the strongest v0.2.0 outcome, but it is still a result in the regularized finite-core filament model, not full volumetric 3-D Euler.

---

# 8. Default runs

## BASIC

```bat
run_all.cmd
```

or explicitly:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\knots\final
```

BASIC uses approximately:

```text
N = 64
Stage A T = 24
absolute discovery = 1.2
minimum holdout cycles = 4
Stage B T = 4, candidates only
```

Outputs:

```text
outputs\basic\analysis\blind_stage_a_summary.json
outputs\basic\analysis\blind_stage_a_modal_results.csv
outputs\basic\analysis\stage_a_candidates.json
outputs\basic\analysis\blind_stage_b_results.csv
outputs\basic\analysis\blind_summary.json
```

Do not reveal identities before inspecting the blind summaries.

## Stage A only

For a cheaper decisive recurrence test:

```bat
run_stage_a_only.cmd
```

This performs no material/fixed Stage B.

## EXTENDED

```bat
run_all_extended.cmd
```

EXTENDED uses:

```text
N = 96
Stage A T = 36
minimum holdout cycles = 6
stricter multi-return/stationarity gates
```

and then runs the N=64/96/128 Stage-A resolution ladder on the preselected high-information carrier trio.

---

# 9. Focus runs

```bat
run_focus_6p3.cmd
run_focus_link_4p2p1.cmd
run_focus_link_9p2p20.cmd
```

These correspond to the previously interesting regimes, but carrier semantics remain hidden from the blind analyzer.

---

# 10. Resolution ladder

```bat
run_resolution.cmd
```

uses:

\[
N=64,96,128,
\qquad T_{\rm StageA}=24
\]

with the same `dt_factor`, so

\[
\Delta t\propto\Delta s^2
\]

is retained.

The resolution comparison requires the same anonymous carrier and the same `natural` or `odd` modal channel to survive. It checks convergence of both period and multi-return closure.

---

# 11. Numerical safety

- RK4 physical integration.
- C++17 / pybind11 / OpenMP O(N^2) regularized Biot-Savart kernel.
- Hard `max_steps`; the code refuses to enlarge `dt` silently.
- `py::ssize_t` is used for Windows/MSVC portability.
- Native backend can be required by config.
- Hard mesh-quality stops are explicit outputs, never silently ignored.

---

# 12. What would count as strong evidence?

The scientifically interesting chain is now deliberately demanding:

\[
\boxed{
\text{multi-cycle recurrent intrinsic mode}
\rightarrow
\text{multi-return closure}
\rightarrow
\text{period/amplitude stationarity}
\rightarrow
\text{stretch coupling}
\rightarrow
\text{measured delay advantage}
\rightarrow
\text{material-core specificity}
}
\]

If Stage A fails even after mesh stabilization and 4–6 complete holdout cycles, the hypothesis of a persistent intrinsic shape-clock receives a substantially stronger negative result than any v0.1.x run could provide.
