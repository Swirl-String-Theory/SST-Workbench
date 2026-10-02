# SST Counter-Pulley Alpha Falsifier v0.5.0

## Purpose

v0.5.0 extends the v0.4 **orbit-first** falsifier with an alpha-blind **Jacobian-free Newton--Krylov multiple-shooting solver** for a counter-rotating `+Gamma/-Gamma` trefoil pair.

The scientific order is strict:

1. validate the Biot--Savart implementation and time integrator;
2. quotient rigid `SE(3)` motion and tangential centerline gauge;
3. test whether a proposed longitudinal `Delta s_+-` is physical or merely relabelling;
4. run an alpha-blind seed campaign;
5. refine the best seed with Newton--Krylov multiple shooting in a preregistered transverse Kelvin/Fourier correction space;
6. require **full Cartesian RPO closure**, not merely projected shooting closure;
7. confirm the RPO at higher resolution;
8. only then construct the true relative-return monodromy `D(g^-1 o phi_T)`;
9. only after H18 may the separate benchmark module import/open alpha.

No alpha-derived quantity enters the orbit search, Newton--Krylov residual, GMRES solve, recurrence score, RPO acceptance or Floquet construction.

## Key correction versus the proposed `Delta s_+-` route

For two complete closed axisymmetric filament curves, a pure longitudinal shift of one filament **along itself** is a reparametrisation in the continuum. It cannot create a new physical vortex configuration. v0.5 therefore does not use `Delta s_+-` as a rescue parameter. Instead H5 verifies numerically that the finite-N effect of fractional channel relabelling decreases with resolution.

A genuinely physical longitudinal phase would require additional material structure (for example a non-axisymmetric finite core or a helical internal vortex-line phase). That is outside the v0.5 model and is not silently introduced.

## Newton--Krylov multiple shooting

Let the nonlinear geometric filament flow be

\[
\frac{d\mathbf X}{d\hat t}=\widehat{\mathbf F}(\mathbf X),
\qquad
\widehat{\mathbf F}=\frac{\mathbf u_\perp}{\Omega_\Gamma},
\qquad
\Omega_\Gamma=\frac{|\Gamma|}{4\pi D^2}.
\]

Tangential velocity is removed because it only changes marker parametrisation:

\[
\mathbf u_\perp=\mathbf u-(\mathbf u\cdot\mathbf t)\mathbf t.
\]

For `M` shooting nodes, v0.5 uses corrected states

\[
\mathbf X_j=\mathbf X_j^{(0)}+D\,\mathbf B_j\mathbf a_j,
\]

where `B_j` is an alpha-independent transverse Fourier/Kelvin basis. The final segment is compared with the first node after one common cyclic shift and one proper rigid `SE(3)` transformation.

The reduced nonlinear system is solved with Newton steps

\[
\mathbf J_F(\mathbf z_k)\,\delta\mathbf z=-\mathbf F(\mathbf z_k),
\]

without forming `J_F`. Matrix-vector products use finite differences,

\[
\mathbf J_F\mathbf v\approx
\frac{\mathbf F(\mathbf z+h\mathbf v)-\mathbf F(\mathbf z)}{h},
\]

and the linear Newton correction is solved by restarted GMRES. A line-search merit includes both the projected residual and full-state segment defect, preventing a low-dimensional projected false positive from counting as progress.

## Hard RPO acceptance

A Newton--Krylov candidate is accepted only if all of the following hold:

\[
\varepsilon_{\rm RPO}
=\frac{\|g^{-1}\phi_T(\mathbf X_0)-\mathbf X_0\|_{\rm RMS}}{D}
<\varepsilon_{\rm gate},
\]

plus endpoint-vectorfield compatibility, cross-channel core separation, bounded segment nonuniformity, and multiple-shooting defect control.

A small projected residual alone **never** opens the Floquet gate.

## H0--H18 protocol

| Gate | Meaning |
|---|---|
| H0 | alpha target absent from blind solver sources |
| H1 | C++/Python RHS parity |
| H2 | RK4 convergence |
| H3 | `SE(3)` quotient correctness |
| H4 | dimensionless scale collapse |
| H5 | longitudinal closed-filament shift converges as gauge |
| H6 | canonical recurrence search well posed |
| H7 | alpha-blind seed campaign well posed |
| H8 | Newton--Krylov solver numerically well posed |
| H9 | multiple-shooting full-state defect decreases materially |
| H10 | full Cartesian RPO closure |
| H11 | endpoint vector-field compatibility |
| H12 | RPO survives higher resolution |
| H13 | true relative monodromy constructed |
| H14 | time-tangent neutral multiplier |
| H15 | monodromy finite-difference convergence |
| H16 | real-monodromy conjugate pairing |
| H17 | finite low-leakage true Floquet readout |
| H18 | permission to import/open alpha benchmark |

## Bundled full native reference result

The full native campaign gives:

- H0--H9: **PASS**;
- H10: **FAIL**;
- H11: **FAIL**;
- H12--H17: **SKIP**;
- H18: **FAIL**;
- alpha opened: **false**.

Best alpha-blind seed before Newton--Krylov:

\[
\frac{a}{D}=0.25,
\qquad
\frac{\epsilon}{D}=0.10,
\qquad
\phi=\frac{\pi}{2},
\qquad
\varepsilon_{\rm RPO}^{\rm seed}=0.4173283240.
\]

The 4-segment, 10-mode Newton--Krylov refinement gives

\[
\hat T=0.1338771061,
\]

\[
\varepsilon_{\rm RPO}=0.3463310365,
\qquad
\varepsilon_f=0.7562101428.
\]

Its projected shooting residual improves by

\[
0.6442244122\rightarrow0.4559781062,
\]

and the maximum full shooting defect improves by

\[
0.3897500535\rightarrow0.3561396051.
\]

Thus the nonlinear solver makes real progress, but the resulting state is still far outside the preregistered full-RPO closure threshold of `0.05 D`.

For the longitudinal relabelling diagnostic,

\[
\epsilon_{\rm relabel}(N=48)=8.7731\times10^{-2},
\]

\[
\epsilon_{\rm relabel}(N=96)=2.4746\times10^{-2},
\]

supporting its interpretation as a finite-discretisation representation of a continuum gauge rather than a new physical degree of freedom.

Machine verdict:

```text
NO_ALPHA_BLIND_RPO_FOUND_AFTER_NEWTON_KRYLOV_MULTIPLE_SHOOTING__TRUE_FLOQUET_GATE_CLOSED
```

## Installation

```bat
install_requirements.cmd
build_native.cmd
native_preflight.cmd
```

`requirements.txt` explicitly contains `setuptools>=70`.

## Main runs

Quick complete protocol:

```bat
run_quick.cmd
```

Full protocol:

```bat
run_full.cmd
```

Standalone Newton--Krylov RPO solver:

```bat
run_newton_krylov.cmd --n 16 --offset 0.25 --eps 0.10 --phase 1.5707963267948966
```

Try true Floquet construction. This exits blocked unless the Newton--Krylov full-state RPO gates accept the orbit:

```bat
run_true_floquet.cmd
```

Explicit blind then post-hoc benchmark:

```bat
run_blind_then_benchmark.cmd
```

## Package layout

- `cpp/native.cpp` -- C++17/pybind11 regularised Biot--Savart kernel.
- `sst_counterpulley/orbit.py` -- geometric filament flow and recurrence search.
- `sst_counterpulley/rpo_solver.py` -- v0.5 longitudinal-gauge diagnostic + Newton--Krylov multiple shooting.
- `sst_counterpulley/monodromy.py` -- true relative-return monodromy, gated behind accepted RPO.
- `sst_counterpulley/blind_gates.py` -- H0--H18 protocol.
- `sst_counterpulley/benchmark.py` -- isolated post-hoc alpha target.
- `reference_native_full/` -- archived full native blind result.
- `reference_native_quick/` -- archived quick native result.
- `reference_fallback_quick/` -- archived Python fallback quick result.

## Scope of the negative result

v0.5 does **not** prove that no relative periodic counter-rotating trefoil pair exists. It excludes the tested finite-core closure, seed family, correction basis, time window and Newton--Krylov trust region at the archived resolutions. A broader state-space continuation or a richer physical core model remains a legitimate next test.

## References

```latex
\bibitem{Floquet1883}
G.~Floquet,
``Sur les équations différentielles linéaires à coefficients périodiques,''
\textit{Annales scientifiques de l'École Normale Supérieure}, Série 2, \textbf{12}, 47--88 (1883).
doi:10.24033/asens.220.

\bibitem{SaadSchultz1986}
Y.~Saad and M.~H.~Schultz,
``GMRES: A Generalized Minimal Residual Algorithm for Solving Nonsymmetric Linear Systems,''
\textit{SIAM Journal on Scientific and Statistical Computing} \textbf{7}, 856--869 (1986).
doi:10.1137/0907058.

\bibitem{KnollKeyes2004}
D.~A.~Knoll and D.~E.~Keyes,
``Jacobian-free Newton--Krylov methods: a survey of approaches and applications,''
\textit{Journal of Computational Physics} \textbf{193}, 357--397 (2004).
doi:10.1016/j.jcp.2003.08.010.

\bibitem{Viswanath2007}
D.~Viswanath,
``Recurrent motions within plane Couette turbulence,''
\textit{Journal of Fluid Mechanics} \textbf{580}, 339--358 (2007).
doi:10.1017/S0022112007005459.
```
