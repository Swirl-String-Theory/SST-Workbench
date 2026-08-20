# SST Trefoil Coupled Torsion–Breathing–Kelvin Balance + RPO/Floquet Falsifier v0.3.0

Blind finite-core Biot–Savart falsifier for the hypothesis that trefoil self-confinement, if it exists, can arise from a **dynamical balance of breathing, torsion-sensitive and Kelvin-like centerline modes**, rather than from a single static cross-lobe repulsion term.

The v0.1 critical decision rule is retained unchanged. v0.3.0 adds deeper diagnostics only; it does **not** move the original PASS/FAIL goalposts.

## Default datasets

```text
C:\workspace\projects\SST-Workbench\KnotPlot\Knots_FourierSeries\3_1\knot.3_1.fseries
C:\workspace\projects\SST-Workbench\KnotPlot\knots\final\knot_3.1_final.txt
```

Byte-identical reproducibility copies are bundled in `repro_inputs/` with SHA-256 hashes.

## One-command run

```bat
run_all.cmd
```

Other entry points:

```bat
run_basic.cmd
run_extended.cmd
run_cpu.cmd
run_gpu_sycl.cmd
run_summarize.cmd <output_directory>
run_reproduce_history_basic.cmd
run_reproduce_history_extended.cmd
```

`run_install.cmd` builds the C++/OpenMP backend. `run_gpu_sycl.cmd` explicitly initializes Intel oneAPI and requires a genuine SYCL load; it does not silently relabel an OpenMP fallback as SYCL.

## Immutable legacy decision rule

Overall campaign PASS/FAIL still uses only:

```text
G0_numerical_sanity
G2_reduced_stability
G3_cross_lobe_stabilizes
G4_nearest_pair_cross_separates
G6_ringdown_bounded
```

All v0.3 gates are diagnostic. This preserves comparability with v0.1.x and v0.2.0.

## v0.3.0 expanded mode basis

The old six-mode basis is retained for the legacy gates. A separate expanded analysis builds

```text
tilt_0..2
breathe_0..2
torsion_0..2
Kelvin-like normal/binormal Fourier modes k = configured harmonics
```

For a uniform arclength coordinate \(s\), Kelvin-like perturbations are generated from the local discrete Frenet frame as

\[
\phi^{N,c}_k(s)=\cos(ks)\,\mathbf n(s),\qquad
\phi^{N,s}_k(s)=\sin(ks)\,\mathbf n(s),
\]

\[
\phi^{B,c}_k(s)=\cos(ks)\,\mathbf b(s),\qquad
\phi^{B,s}_k(s)=\sin(ks)\,\mathbf b(s).
\]

The torsion-sensitive lobe modes are smooth lobe-windowed binormal displacements. They are centerline perturbations intended to alter local out-of-plane curvature/torsion; they are not an independent material twist degree of freedom.

Rigid translation, rigid rotation and tangential reparameterization are removed before projection.

## Coupled Jacobian and causal family ablations

The expanded finite-difference Jacobian is computed at multiple \(\epsilon\) values and checked for convergence.

For family indices \(B,T,K\) denoting breathing, torsion and Kelvin families, v0.3.0 compares the full matrix with counterfactual matrices in which off-diagonal couplings to a selected family are zeroed.

A positive quantity

\[
\Delta g_T=
\frac{\max\Re\lambda(J_{\rm decouple\,T})-\max\Re\lambda(J)}{\rho(J)} > 0
\]

means torsion coupling lowered the worst resolved growth rate. Analogous quantities are computed for breathing and Kelvin coupling, plus a completely family-block-diagonal counterfactual.

These are **reduced-model causal ablations**, not new forces inserted into the physical Biot–Savart solver.

## RPO search

The expanded spectrum is searched for an oscillatory eigenmode with simultaneous breathing/torsion/Kelvin participation. The real/imaginary parts of that eigenvector define a phase family of finite perturbations.

Each phase is evolved nonlinearly. Rigid motion is removed by Kabsch alignment, and shape recurrence is measured by normal displacement from the initial curve.

A phase cannot qualify as a relative-periodic-orbit candidate merely because it drifts slowly. It must satisfy all of:

1. first leave the initial shape by at least `rpo_excursion_min`;
2. later return below `rpo_recurrence_max`;
3. reduce recurrence relative to its earlier peak by `rpo_return_ratio_max`;
4. avoid a near-core event.

This prevents the trivial false positive “the trajectory stayed close because almost no time passed”.

## Phase locking

Only a valid RPO candidate is subjected to the phase-lock diagnostic. Dominant breathing, torsion and Kelvin coordinates are split into time windows. v0.3.0 tests whether their dominant frequencies agree and whether their pairwise phase differences remain coherent across windows.

## Conditional nonlinear Floquet test

Floquet analysis is **gated by RPO recurrence**. Without a passing recurrence, `G19` fails diagnostically and no monodromy matrix is interpreted.

For a valid return after \(T\), the nonlinear return map is finite-differenced:

\[
M_{ij}
\approx
\frac{q_i\!\left(\Phi_T[X_0+\epsilon\phi_j]\right)
-q_i\!\left(\Phi_T[X_0-\epsilon\phi_j]\right)}{2\epsilon}.
\]

The Floquet multipliers are

\[
\mu_i=\operatorname{eig} M.
\]

One multiplier nearest \(1\) is reported as the candidate neutral phase direction; the preregistered stability gate uses the largest remaining \(|\mu_i|\). This is a finite-dimensional projected return map, not a proof of full infinite-dimensional Euler stability.

## v0.3 diagnostic gates

```text
G12_TBK_mode_resolved
G13_torsion_coupling_stabilizes
G14_kelvin_coupling_stabilizes
G15_breathing_coupling_stabilizes
G16_TBK_collective_coupling_stabilizes
G17_TBK_phase_lock
G18_RPO_recurrence
G19_Floquet_bounded
```

Every run writes a prose conclusion, measurements and thresholds for every gate.

## Outputs

```text
REPORT.md
GATE_CONCLUSIONS.md
gate_conclusions.json
summary_metrics.csv
modal_attribution.csv
contact_pairs.csv
component_ablation.csv
coupled_spectrum.csv
family_coupling_ablation.csv
phase_lock.csv
rpo_phase_scan.csv
floquet_multipliers.csv
plots/
pre_unblind/
```

Large numerical arrays, including the expanded mode basis, selected coupled Jacobians and a valid Floquet monodromy matrix, are retained in each blind `*_arrays.npz`.

## No hidden topology or repulsion operator

The package contains no `reconnect()`, cut/splice, contact penalty, hard-core bounce, or hand-written restoring force. Near-core events terminate/report the affected diagnostic instead of altering topology.

## Reproducibility chain

This release contains immutable ZIP snapshots:

```text
release_history/
  SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.0.zip
  SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.1.1.zip
  SST_Trefoil_Lobe_Orientation_Blind_Falsifier_v0.2.0.zip
```

The historical runners unpack and execute each archived version with its own old code/config against the same bundled inputs, followed by v0.3.0.

## SST dimensional mapping

Normalized calculations use \(\Gamma=1\) and total centerline length \(2\pi\). Physical reporting uses

\[
\Gamma_{\rm SST}=2\pi r_c\mathbf{v}_{\!\boldsymbol{\circlearrowleft}},
\]

with

\[
r_c=1.40897017\times10^{-15}\ \mathrm{m},\qquad
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=1.09384563\times10^6\ \mathrm{m\,s^{-1}},
\]

so

\[
\Gamma_{\rm SST}=9.68361920349\times10^{-9}\ \mathrm{m^2\,s^{-1}}.
\]

A convenience BASIC validation snapshot is included under `reference_results/v0.3.0_basic/`; it is not used as an expected-answer oracle and can be recomputed from the bundled inputs.

See `docs/PREREGISTRATION.md`, `docs/HISTORICAL_REFERENCE_CONCLUSIONS.md`, `docs/REPRODUCIBILITY.md`, `docs/REFERENCES.tex`, and `CHANGELOG.md`.
