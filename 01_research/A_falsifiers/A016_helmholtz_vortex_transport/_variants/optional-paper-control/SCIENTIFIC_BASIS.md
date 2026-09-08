# Helmholtz -> SST gate map

The package deliberately separates what a static relaxed centerline can test from what Helmholtz's time-dependent theorems require.

## H0 — closed-filament/data integrity

Helmholtz's vortex lines/filaments do not terminate freely in the ideal fluid. On a static centerline dataset this can only be used as a geometry precondition, not as evidence of temporal persistence.

## H1 — numerical convergence

The self-induced velocity is nonlocal. The finite-core line integral is evaluated at two resolutions so a claimed dynamical conclusion cannot be a discretization artifact.

## H2 — holonomy/topology consistency

Outside the vortex filament Helmholtz permits a locally potential flow in a multiply connected region with a multivalued potential. The numerical line integral around local meridian loops is therefore checked against integer circulation/linking structure. This is a numerical/topological consistency gate, not a derivation of quantum phase.

## H3 — relative-equilibrium falsifier

A curved vortex generally self-propels. Therefore a particle candidate should not be required to have zero induced velocity; its *shape* should be stationary modulo rigid translation, rigid rotation, and tangential reparameterization:

\[
\mathbf v_{\rm ind}(\mathbf X(s))
=\mathbf U+\boldsymbol\Omega\times[\mathbf X(s)-\mathbf X_0]+\lambda(s)\mathbf t(s).
\]

The gate minimizes the normal residual after fitting `U` and `Omega`. Failure is the main scientific falsifier in this static-centerline workbench.

## H4 — circulation/mirror symmetry

Reversing centerline orientation reverses the unit-circulation Biot--Savart field. Reflection is audited separately so geometric chirality and circulation direction are not silently conflated.

## Finite-core energy diagnostic

For the regularized centerline kernel the package reports

\[
E=\rho\Gamma^2\,\ell_E,
\]

where `ell_E` is the computed `energy_length_reference`. The blind run does **not** decide whether `rho` should be `rho_f` or `rho_core`. Reveal reports both interpretations separately.

## rho_f and the torsion pulse

The SST research-track separation retained here is

\[
\mathcal L_{\rm torsion}
=\frac12\rho_{\!f}|\partial_t\mathbf A|^2
-\frac12K|\nabla\times\mathbf A|^2,
\qquad
c_T^2=K/\rho_{\!f},
\qquad
Z_{\rm torsion}=\rho_{\!f}c_T.
\]

A static relaxed knot has no `A(x,t)` data, so the core--torsion impedance lemma is marked `NOT_TESTED_BY_STATIC_CENTERLINE_DATA` rather than manufactured from geometry proxies.

## Source status

Helmholtz-derived concepts: persistence of vortex lines, constancy of filament strength/cross-section product under the stated ideal-flow assumptions, nonlocal velocity reconstruction, multiply-connected potential behavior, finite-core necessity for curved filaments, energy conservation under closed boundary conditions, and self-motion/interactions of rings.

SST-specific hypotheses: mapping the relaxed knot to a particle candidate, mapping the core-radius proxy to `r_c`, the two-density interpretation, and any mass/clock/torsion closure. These are not claims of Helmholtz's paper.

## LaTeX bibliography entries

```latex
\\bibitem{Helmholtz1858}
H.~von Helmholtz,
``Uber Integrale der hydrodynamischen Gleichungen, welche den Wirbelbewegungen entsprechen,''
\\textit{Journal fur die reine und angewandte Mathematik} \\textbf{55}, 25--55 (1858).

\\bibitem{Moffatt1969}
H.~K. Moffatt,
``The degree of knottedness of tangled vortex lines,''
\\textit{Journal of Fluid Mechanics} \\textbf{35}, 117--129 (1969).
DOI: 10.1017/S0022112069000991.

\\bibitem{Saffman1992}
P.~G. Saffman,
\\textit{Vortex Dynamics},
Cambridge University Press (1992).
```
