# SST Threaded-Hole Substrate Blind Falsifier v0.3.0

Blind C++17/pybind11 + Python workbench for the question

\[
\boxed{\text{Is the central threaded hole a robust dynamical structure, or only a visual gap in centerline geometry?}}
\]

v0.3.0 keeps all v0.2.1 self-confinement, pressure-Poisson, thread-focusing, similarity and triple-gear gates, and adds a dedicated **Kelvin--M'Farlane Lagrangian threaded-hole gate**.

## What is new in v0.3.0

1. **Kelvin--M'Farlane analytic oracle** before any blind campaign.
2. **Geometry-only hole-axis search**: the blind runner does not read knot family or private axis labels.
3. **Co-moving flow field** with best-fit rigid translation and rotation removed:
   \[
   \mathbf u_{\rm rel}(\mathbf x)=\mathbf u(\mathbf x)-\mathbf U-\boldsymbol\Omega\times(\mathbf x-\mathbf c).
   \]
4. **Frozen Lagrangian/streamline connectivity test** with deterministic seeds, integrated by arclength so slow flow is not misclassified merely because an arbitrary observation time was too short.
5. Classification into `OPEN_CHANNEL`, `CAPTURED_ATMOSPHERE`, `TRANSITIONAL_PINCH`, or `VISUAL_ONLY_OR_INCOHERENT`.
6. **Finite carrier evolution** followed by a fresh transport re-test after rigid alignment.
7. **Normal-mode perturbation persistence** with preregistered \(\pm\epsilon\) perturbations.
8. A target-independent **hole robustness score/cost** for blind A/B ranking.
9. **Two-layer post-seal reveal**: first whether a dynamical hole exists at all, then whether nonzero closed-thread circulation causally improves it over an **identical visible zero-circulation control**.
10. Causal inference uses the preregistered anonymous multi-cost winner sealed before reveal; no favorable metric is selected post hoc.
11. C++/OpenMP `field_velocity` remains the hot kernel used repeatedly by the tracer integrator.

## Why the null control is strong

Each blind active/null pair has exactly the same:

- carrier centerline;
- closed thread centerlines;
- thread count, pitch and return-leg geometry;
- discretization and regularization parameters.

The only physical difference is

\[
\Gamma_{\rm thread}=0
\]

for the null versus a hidden non-zero circulation for the active condition.

Therefore both candidates contain the same **visible central hole**. If the active condition develops a more persistent Lagrangian channel while the null does not, that difference cannot be attributed to merely seeing a hole in the centerline geometry.

## Kelvin--M'Farlane oracle

For two straight opposite vortices at \(x=\pm a\),

\[
U=\frac{\Gamma}{4\pi a}.
\]

Kelvin/M'Farlane's carried-fluid separatrix can be written

\[
\ln N=\frac{x+b}{a},
\qquad
N=\frac{(x+a)^2+y^2}{(x-a)^2+y^2},
\]

or

\[
\frac{y^2}{a^2}
=
2\frac{x}{a}\coth\!\left(\frac{x+b}{2a}\right)
-1-\frac{x^2}{a^2}.
\]

For \(b=0\) the oracle must recover

\[
\frac{y_s}{a}=\sqrt{3},
\qquad
\frac{x_{\rm edge}}{a}\approx2.087253791,
\]

and the implicit streamline residual must be numerically negligible.

Run only the analytic oracle:

```cmd
run_00_install.cmd
run_01_build_native.cmd
run_kelvin_oracle.cmd
```

## Hole classification

The central passage is estimated from the anonymous carrier geometry alone. Frozen co-moving streamlines are then traced with the equivalent arclength reparameterization \(d\mathbf x/ds=\mathbf u_{\rm rel}/|\mathbf u_{\rm rel}|\). For a steady field this preserves trajectory geometry while removing an arbitrary time-window bias from the topology classification.

- `OPEN_CHANNEL`: enough upstream seeds cross the downstream gate with limited lateral loss.
- `CAPTURED_ATMOSPHERE`: enough central seeds remain in the moving central region.
- `TRANSITIONAL_PINCH`: the center is near a co-moving axial stagnation transition.
- `VISUAL_ONLY_OR_INCOHERENT`: geometric clearance exists, but neither coherent channel nor captured atmosphere is established.

A final `ROBUST_*` verdict additionally requires:

- successful finite carrier evolution;
- retained central clearance;
- the same transport class after evolution;
- robustness over both signs of preregistered normal perturbations;
- persistence of the **same** transport class over those perturbations.

Thus

\[
\text{geometric clearance}>0
\]

is **never** by itself a pass.

## Blind score

The blinded candidate cost combines only anonymous, target-independent diagnostics:

\[
C_{\rm hole}=1-S_{\rm hole},
\qquad 0\le S_{\rm hole}\le1,
\]

where \(S_{\rm hole}\) combines initial/final Lagrangian support, clearance persistence, perturbation robustness and class persistence. The default pair decision also includes separate geometry-collapse, class-instability and Lagrangian-incoherence costs.

No knot name, active/null identity, expected sign, Kelvin critical number, gravitational exponent, \(\alpha\), or SST canon target enters the blind ranking.

## One-command Windows runs

### Basic confirmatory-style hole campaign

```cmd
run_all.cmd
```

or explicitly:

```cmd
run_all_hole.cmd
```

This performs:

```text
install
 -> native C++ build
 -> pytest
 -> Kelvin/M'Farlane analytic oracle
 -> blinded campaign preparation
 -> blinded numerical run
 -> SHA-256 sealing
 -> post-seal reveal
```

### Extended campaign

```cmd
run_all_hole_extended.cmd
```

The extended preset increases spatial resolution, tracer count, perturbation modes, circulation values, \(\beta\) values and helix strata. Expect a substantially longer run.

## Strict manual blind workflow

For a real preregistered run, do not immediately reveal:

```cmd
run_00_install.cmd
run_01_build_native.cmd
run_tests.cmd
run_kelvin_oracle.cmd
run_kelvin_hole_basic_prepare.cmd
run_kelvin_hole_basic_blind.cmd
```

Archive the blind directory and its seal first. Only then run:

```cmd
run_kelvin_hole_basic_reveal.cmd
```

## Main v0.3.0 outputs

```text
outputs\kelvin_hole_basic\blind\blind_summary.json
outputs\kelvin_hole_basic\blind\blind_pair_results.csv
outputs\kelvin_hole_basic\blind\cases\*.json
outputs\kelvin_hole_basic\reveal\HOLE_REVEAL_SUMMARY.json
outputs\kelvin_hole_basic\reveal\hole_revealed_pairs.csv
outputs\kelvin_hole_basic\reveal\HOLE_CONCLUSIONS.md
outputs\kelvin_hole_basic\reveal\REVEAL_SUMMARY.json
outputs\kelvin_hole_basic\reveal\CONCLUSIONS.md
```

Each case JSON retains the full anonymous diagnostic, including hole axis, clearance, stagnation scan, tracer fractions, finite-evolution result and every perturbation result.

## Interpretation

The reveal deliberately answers **two different questions**.

1. **Existence:** does either arm exhibit a robust Lagrangian open channel or captured vortex atmosphere? If neither does, the visible centerline hole is reported as dynamically unestablished within the tested model/horizon.
2. **Causal role of the central thread circulation:** after seal verification, does the active arm systematically beat the geometrically identical zero-circulation control under the *already sealed* multi-cost blind decision?

A robust hole in **both** arms is therefore not called evidence for the thread circulation. It instead indicates a carrier-generated or thread-independent dynamical hole. Conversely, an active-only robust signal plus a carrier-clustered sealed active advantage is evidence that thread circulation contributes within the tested model.

None of these outcomes by itself establishes an SST particle model, an exact Euler solution, or infinite-time material confinement. A null/adverse result remains informative: geometry alone is never used to rescue a failed dynamical gate.

## Existing v0.2.1 gates retained

The previous workbench remains available in the same package:

- self-confinement / relative-equilibrium dynamics;
- free-space pressure-Poisson source and monopole test;
- free far-field exponent;
- pressure/source convergence ladder;
- active-thread vs passive-tracer focusing;
- circulation similarity;
- fixed-per-thread density scans;
- triple-gear marker-invariant phase proxy.

The new default `run_all.cmd` targets the Kelvin threaded-hole question. Legacy `run_all_*` commands are retained.

## References

See `docs/REFERENCES.tex` for copy-ready `\bibitem` entries.
