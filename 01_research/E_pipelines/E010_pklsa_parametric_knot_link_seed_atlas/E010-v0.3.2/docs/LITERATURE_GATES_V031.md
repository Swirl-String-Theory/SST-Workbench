# PKLSA v0.3.1 — literature-derived geometry gates

PKLSA v0.3.1 adds a separate literature-gate layer on top of the existing source, topology, and per-observable convergence checks. The gates are intentionally split into **hard geometry-integrity gates** and **soft/contextual benchmarks or diagnostics**. A contextual benchmark is not promoted to a universal hard gate when its assumptions do not hold for every carrier.

## Gate inventory

| Gate | Class | Default publication behavior | Numerical criterion / output | Scientific basis |
|---|---|---|---|---|
| `G1_isotopy_safe_sampling` | hard | enforced | Each reconstructed sampling interval has estimated total curvature below \(\pi/2\); a curvature-based chord-deviation bound must remain inside `isotopy_tube_fraction * reach` | Li & Peters isotopic-convergence sufficient conditions |
| `G2_writhe_quadratic_convergence` | hard | enforced | Exact polygonal writhe is evaluated over the resolution ladder; local convergence order must satisfy `p >= writhe_order_min` (publication default 1.5) or be numerically exact | Cantarella smooth-curve vs inscribed-polygon writhe bound, asymptotically \(O(N^{-2})\) |
| `G3_signed_frenet_chirality_completeness` | hard | enforced | Signed torsion integral and signed writhe must be retained | Liu et al.: \(\{\kappa,|\tau|\}\) does not in general determine chirality and can admit multiple branches |
| `B1_ideal_trefoil_ropelength` | contextual benchmark | reported, not hard by default | For explicitly ideal-like `3_1` carriers, compare recomputed `Rop=L/Thi` with 16.3714672385; audit an upstream reference value separately when present | Przybyl & Pierański high-resolution ideal trefoil |
| `B2_torus_analytic_geometry` | contextual benchmark | reported | For carriers that declare `torus_p`, `torus_q`, `torus_lambda`, emit \(\lambda_{cr}=1/(1+w^2)\), crossing diagnostics, and analytic length comparison if \(R\) is known | Oberti & Ricca torus-knot geometry |
| `D1_hasimoto_phase_holonomy` | diagnostic | never hard | Emit \(\int\tau\,ds\pmod{2\pi}\) per component | Hasimoto transform; Brizard closed-elastica/NLSE closure analysis |
| `D2_vortex_dynamics_handoff` | diagnostic | never hard | Mark geometry `READY` only when a positive core-scale proxy (`reach`) and signed writhe are present | Maggioni et al.; Kivotides & Leonard vortex-knot/link dynamics |

## G1: isotopy-safe sampling proxy

Li & Peters give sufficient conditions for an inscribed PL approximation to preserve knot type. PKLSA cannot turn a finite numerical estimate into an exact ambient-isotopy theorem, so v0.3.1 implements a conservative numerical proxy.

For each sampling interval \(i\),

\[
K_i^{\rm est}
=\frac{\kappa_i+\kappa_{i+1}}{2}\,\Delta s_i
<\frac{\pi}{2}.
\]

The interpolation chord deviation is bounded locally by the circular-arc approximation

\[
\delta_i^{\rm chord}\lesssim \frac{\kappa_{\max} h_{\max}^2}{8},
\]

and the gate additionally requires

\[
\delta_i^{\rm chord}
<f_{\rm tube}\,\operatorname{reach}(C),
\qquad f_{\rm tube}=0.5\ \text{by default}.
\]

The first condition approximates the subcurve-total-curvature criterion; the second is a numerical containment proxy for staying inside a non-self-intersecting tubular neighborhood. `G1` is therefore explicitly labelled a **sufficient-condition proxy**, not a proof certificate.

## G2: exact polygonal writhe + convergence order

v0.3.0 evaluated the Gauss integral with segment-midpoint quadrature. That is no longer used for `Wr`, `ACN`, or linking number. v0.3.1 analytically integrates each pair of straight polygonal segments by its oriented solid angle.

For one oriented triangle with vectors \(\mathbf a,\mathbf b,\mathbf c\), the implemented stable form is

\[
\Omega(\mathbf a,\mathbf b,\mathbf c)
=2\operatorname{atan2}\!\left(
\mathbf a\cdot(\mathbf b\times\mathbf c),
|\mathbf a||\mathbf b||\mathbf c|
+(\mathbf a\cdot\mathbf b)|\mathbf c|
+(\mathbf b\cdot\mathbf c)|\mathbf a|
+(\mathbf c\cdot\mathbf a)|\mathbf b|
\right).
\]

The quadrilateral subtended by two straight segments is split into two such spherical triangles. The polygonal Gauss integral is then exact up to floating-point roundoff.

For a quasi-geometric ladder, PKLSA estimates

\[
p_i =
\frac{\ln\!\left(|W_{N_i}-W_{N_{i+1}}|/|W_{N_{i+1}}-W_{N_{i+2}}|\right)}
{\ln r},
\]

with \(r\) the local refinement ratio. Cantarella's result motivates the asymptotic target \(p\to2\); the publication threshold is deliberately looser (`1.5`) to tolerate pre-asymptotic numerical data without pretending that any positive trend is enough.

## G3: signed Frenet/chirality completeness

The qualified carrier now stores at every resolution

\[
T_{\tau}=\oint \tau(s)\,ds,
\]

plus signed `Wr`. This prevents the identity layer from silently reducing a curve to \(\{\kappa(s),|\tau(s)|\}\).

Liu et al. show that unsigned torsion can lose mirror information and, for non-generic branch structures, can admit more than a simple mirror pair. PKLSA therefore records the signed data and emits a warning that the exact branch invariant \(c(\tau)\), which depends on infinite-order torsion zeros, cannot be certified from finite samples.

## B1: ideal trefoil benchmark and the radius/diameter convention

Przybyl & Pierański report the radius-convention ideal-trefoil ropelength

\[
L/R = 32.742934477,
\]

which in PKLSA's historical diameter convention becomes

\[
\boxed{L/D = 16.3714672385}.
\]

`B1` deliberately distinguishes two questions:

1. does an upstream ideal-knot reference value agree with the literature benchmark?;
2. does PKLSA's **recomputed** `reach/dcsd` estimator reproduce the same ropelength?

This separation prevents a good source reference from hiding a biased internal thickness estimator, or vice versa.

## B2: torus-knot analytic control

For the standard \(T_{p,q}\) parametrization, with

\[
w=\frac{q}{p},\qquad \lambda=\frac rR,
\]

PKLSA reports the critical aspect ratio

\[
\lambda_{\rm cr}=\frac{1}{1+w^2}
\]

and the minimum crossing number

\[
c_{\min}=\min\{p(q-1),q(p-1)\}.
\]

When `torus_major_radius` is also declared, the analytic normalized length

\[
\frac{L}{2\pi R}
=\frac{1}{2\pi}
\int_0^{2\pi p}
\sqrt{(1+\lambda\cos w\alpha)^2+\lambda^2w^2}\,d\alpha
\]

is compared against the native carrier length before normalization.

## Diagnostics D1–D2

The Hasimoto phase diagnostic is

\[
\Phi_H = \oint \tau(s)\,ds \pmod{2\pi}.
\]

It is **not** a claim that a generic PKLSA carrier solves the localized-induction equation or the nonlinear Schrödinger equation. Likewise `D2` only declares that geometry contains enough scale/orientation information to be handed to a later finite-core/Biot–Savart calculation; it does not infer circulation, Reynolds number, core profile, reconnection behavior, or stability.

## Publication configuration

`configs/qualification_publication.json` sets:

```json
{
  "literature_gates": true,
  "literature_gate_mode": "enforce",
  "isotopy_turn_limit_rad": 1.5707963267948966,
  "isotopy_tube_fraction": 0.5,
  "writhe_order_min": 1.5,
  "writhe_order_numeric_floor": 1e-10,
  "ideal_trefoil_rel_tol": 0.01,
  "enforce_ideal_trefoil_benchmark": false,
  "torus_length_rel_tol": 0.005
}
```

The ideal-trefoil gate remains soft until the numerical `reach/dcsd` estimator itself is separately certified against ideal-knot contact geometry.

## References (copy-ready LaTeX)

```latex
\begin{thebibliography}{99}

\bibitem{LiPeters2013}
J.~Li and T.~J.~Peters,
``Isotopic Convergence Theorem,''
\emph{Journal of Knot Theory and Its Ramifications} \textbf{22} (2013), 1350012.
\doi{10.1142/S0218216513500120}.

\bibitem{Cantarella2002Writhe}
J.~Cantarella,
``On Comparing the Writhe of a Smooth Curve to the Writhe of an Inscribed Polygon,''
\emph{SIAM Journal on Numerical Analysis} \textbf{42} (2004), 1846--1861.
\doi{10.1137/S0036142902403164}.

\bibitem{LiuEtAl2026UnsignedFrenet}
J.~Liu, W.~Wang, Q.~Tian, and W.~Wang,
``Unsigned Frenet Data of Closed Space Curves: Exact Fibres, Generic Rigidity, and Conditional Stability,''
\emph{arXiv:2608.09194} (2026).
\url{https://arxiv.org/abs/2608.09194}.

\bibitem{PrzybylPieranski2014}
S.~Przybyl and P.~Piera\'nski,
``High resolution portrait of the ideal trefoil knot,''
\emph{Journal of Physics A: Mathematical and Theoretical} \textbf{47} (2014), 285201.
\doi{10.1088/1751-8113/47/28/285201}.

\bibitem{AshtonEtAl2011}
T.~Ashton, J.~H.~Cantarella, M.~Piatek, and E.~J.~Rawdon,
``Knot Tightening by Constrained Gradient Descent,''
\emph{Experimental Mathematics} \textbf{20} (2011), 57--90.
\doi{10.1080/10586458.2011.544581}.

\bibitem{ObertiRicca2016}
C.~Oberti and R.~L.~Ricca,
``On torus knots and unknots,''
\emph{Journal of Knot Theory and Its Ramifications} \textbf{25} (2016), 1650036.
\doi{10.1142/S021821651650036X}.

\bibitem{MaggioniEtAl2010}
F.~Maggioni, S.~Z.~Alamri, C.~F.~Barenghi, and R.~L.~Ricca,
``Velocity, energy, and helicity of vortex knots and unknots,''
\emph{Physical Review E} \textbf{82} (2010), 026309.
\doi{10.1103/PhysRevE.82.026309}.

\bibitem{KivotidesLeonard2020}
D.~Kivotides and A.~Leonard,
``Helicity spectra and topological dynamics of vortex links at high Reynolds numbers,''
\emph{Journal of Fluid Mechanics} \textbf{911} (2021), A25.
\doi{10.1017/jfm.2020.1003}.

\bibitem{Hasimoto1972}
H.~Hasimoto,
``A soliton on a vortex filament,''
\emph{Journal of Fluid Mechanics} \textbf{51} (1972), 477--485.
\doi{10.1017/S0022112072002307}.

\bibitem{Brizard2026}
A.~J.~Brizard,
``Nonlinear Schr\"odinger equation on a closed 3D elastica knot,''
\emph{arXiv:2607.21750} (2026).
\url{https://arxiv.org/abs/2607.21750}.

\end{thebibliography}
```
