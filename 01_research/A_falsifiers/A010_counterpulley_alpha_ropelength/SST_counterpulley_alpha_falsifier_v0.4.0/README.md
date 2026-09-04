# SST Counter-Pulley Alpha Falsifier v0.4.0

## Relative-Periodic-Orbit + True Floquet Monodromy

v0.4.0 is an **orbit-first, alpha-blind falsification package** for the counter-rotating `+Gamma/-Gamma` trefoil-channel idea.

The central rule is stricter than v0.3:

> **No relative periodic orbit (RPO) -> no Floquet monodromy -> no alpha benchmark.**

The package retains the C++17/pybind11 Biot--Savart backend and Python fallback from the SST template, but replaces the frozen local eigenmode interpretation of v0.3 by a nonlinear time-domain search for

\[
\mathbf X(\hat T) \simeq g\,\mathbf X(0),
\qquad g\in SE(3),
\]

with one common cyclic relabelling of both closed filaments allowed as a tangential parametrisation gauge.

## Geometric filament gauge

The raw Biot--Savart velocity is unchanged. For **shape evolution** the orbit integrator removes the local tangential velocity,

\[
\mathbf u_\perp
=\mathbf u-(\mathbf u\cdot\mathbf t)\mathbf t,
\]

because tangential motion relabels points along a filament but does not change the embedded centerline shape. This prevents marker clustering from being counted as physical non-recurrence.

Dimensionless time is

\[
\hat t=\Omega_\Gamma t,
\qquad
\Omega_\Gamma=\frac{\Gamma_{\rm scale}}{4\pi D^2}.
\]

No measured value of alpha appears in `orbit.py`, `monodromy.py`, or `blind_gates.py`.

## Relative recurrence metric

For every eligible snapshot the code minimizes

\[
\varepsilon_{\rm RPO}(T)
=
\frac{1}{D}
\min_{g\in SE(3),\,q\in\mathbb Z_N}
\left[
\frac{1}{2N}
\sum_{a=\pm}\sum_{i=1}^N
\left\|
 g\,\mathbf X_{a,i+q}(T)-\mathbf X_{a,i}(0)
\right\|^2
\right]^{1/2}.
\]

The same cyclic shift `q` is applied to both channels. Independent shifts are forbidden because they would tune away their relative phase.

A candidate must also satisfy endpoint vector-field covariance under the *same* fixed group element:

\[
\varepsilon_f
=
\frac{\|g_* f(\mathbf X(T))-f(\mathbf X(0))\|}
{\|f(\mathbf X(0))\|}.
\]

## True relative Floquet map

Only if an RPO passes does v0.4 construct

\[
\boxed{
\mathbf M
=
D\!\left(g_*^{-1}\circ\phi_T\right)_{\mathbf X_0}
}
\]

by central finite differences of the **full nonlinear time-\(T\) flow map**. This is not the frozen Jacobian `exp(J T)` used diagnostically in v0.3.

The package then checks the time-tangent neutral direction,

\[
\frac{\|\mathbf M f_0-f_0\|}{\|f_0\|},
\]

finite-difference convergence, complex-conjugate spectral closure of the real monodromy, and a preregistered Kelvin-subspace readout.

## H0--H14 protocol

| Gate | Meaning |
|---|---|
| H0 | alpha target absent from blind RPO/Floquet modules |
| H1 | native/Python Biot--Savart RHS parity |
| H2 | RK4 asymptotic convergence |
| H3 | exact `SE(3)` quotient test |
| H4 | dimensionless scale collapse |
| H5 | recurrence search is finite/well posed |
| H6 | canonical `a/D=0.5` seed closes |
| H7 | canonical endpoint vector field closes |
| H8 | **some preregistered alpha-blind seed is an RPO** |
| H9 | full relative monodromy is constructed |
| H10 | time-tangent neutral multiplier check |
| H11 | monodromy FD convergence |
| H12 | real-spectrum conjugate pairing |
| H13 | true Kelvin/Floquet phase is defined and low-leakage |
| H14 | permission to import/open the alpha benchmark |

H6/H7 are canonical controls. A noncanonical preregistered seed may still open H8; selection is **only by recurrence quality**, never by alpha proximity.

## Reference result bundled with v0.4.0

The bundled full native reference campaign used 36 preregistered seeds and returned:

- H0--H5: **PASS**
- H6: **FAIL**
- H7: **FAIL**
- H8: **FAIL**
- H9--H13: **SKIP** (scientifically locked)
- H14: **FAIL**

Canonical full run:

\[
\hat T_{\rm best}=0.21,
\qquad
\varepsilon_{\rm RPO}=0.7019664,
\qquad
\varepsilon_f=1.2224031.
\]

The canonical trajectory reached cross-channel core overlap at approximately

\[
\hat t=1.59.
\]

Best seed from the 36-case full blind scan:

\[
\frac{a}{D}=0.30,
\qquad
\frac{\epsilon}{D}=0.10,
\qquad
\phi=\frac{\pi}{2},
\]

with

\[
\hat T_{\rm best}=0.20,
\qquad
\varepsilon_{\rm RPO}=0.4090415,
\qquad
\varepsilon_f=0.5595703.
\]

This is not close enough to an RPO. Therefore the bundled reference verdict is

```text
NO_ALPHA_BLIND_RPO_FOUND_IN_PREREGISTERED_WINDOW__TRUE_FLOQUET_GATE_CLOSED
```

and the post-hoc benchmark remains **unopened**.

This result does **not** prove that no RPO exists at longer periods, at different finite-core closures, or outside the preregistered seed domain. It says that the present two-channel construction has not earned a true-Floquet interpretation yet.

## Commands

```bat
install_requirements.cmd
build_native.cmd
native_preflight.cmd
run_quick.cmd
run_full.cmd
run_rpo_search.cmd
run_true_floquet.cmd
```

Strict staged workflow:

```bat
python run_blind.py --out-dir audit_out_blind
python run_benchmark.py audit_out_blind\blind_audit_summary.json
```

The second command returns a blocked benchmark unless H14 is true; when blocked, it does not import the module containing the numerical alpha target.

## Key files

- `sst_counterpulley/orbit.py` -- geometric-gauge RK4 evolution, `SE(3)` + cyclic recurrence search.
- `sst_counterpulley/monodromy.py` -- full relative-return finite-difference monodromy.
- `sst_counterpulley/blind_gates.py` -- H0--H14 protocol.
- `sst_counterpulley/benchmark.py` -- isolated post-hoc alpha module.
- `cpp/native.cpp` -- native regularized Biot--Savart kernel.
- `data/ideal_3_1_1.txt` -- embedded `3:1:1` ideal-trefoil coefficients.

## References

```latex
\bibitem{Floquet1883}
G.~Floquet,
``Sur les équations différentielles linéaires à coefficients périodiques,''
\textit{Annales scientifiques de l'École Normale Supérieure}, 2e série, \textbf{12}, 47--88 (1883).
doi:10.24033/asens.220.

\bibitem{Hasimoto1972}
H.~Hasimoto,
``A soliton on a vortex filament,''
\textit{Journal of Fluid Mechanics} \textbf{51}, 477--485 (1972).
doi:10.1017/S0022112072002307.

\bibitem{Viswanath2007}
D.~Viswanath,
``Recurrent motions within plane Couette turbulence,''
\textit{Journal of Fluid Mechanics} \textbf{580}, 339--358 (2007).
doi:10.1017/S0022112007005459.
```
