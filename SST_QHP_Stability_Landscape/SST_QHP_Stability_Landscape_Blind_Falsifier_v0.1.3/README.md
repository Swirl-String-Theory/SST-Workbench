# SST QHP Stability Landscape Blind Falsifier v0.1.3

Purpose: test whether a controlled KnotPlot QHP geometry sweep contains a **finite-core vortex-dynamical restoring fixed point** rather than only a geometric/ropelength optimum.

This release corrects three methodological issues exposed by the first real `knot_6.3` campaign: Q breathing was being normalized away, the projection basis was not dimensionally consistent across the 1-D star, and a negative short-time slope could be counted without an actual short-time zero crossing.

## 1. QHP coordinates

The companion generator defines local geometry coordinates around one source seed:

- **Q** — centroid-radial normal-plane breathing;
- **H** — traceless axial flatten/elongation;
- **P** — periodic phase/shear along the closed centerline.

The intended local representation is

\[
\mathbf X(q,h,p)\simeq \mathbf X_0
+q\,\partial_q\mathbf X
+h\,\partial_h\mathbf X
+p\,\partial_p\mathbf X.
\]

## 2. Family-anchor scale normalization

**Critical v0.1.3 change:** do not normalize every candidate independently to \(R_g=1\). Q is a breathing degree of freedom, so per-candidate normalization erases the very expansion/collapse being tested.

v0.1.3 uses

\[
\widetilde{\mathbf X}_{\xi}
=\frac{\mathbf X_{\xi}-\mathbf X_{\xi,\rm cm}}{R_{g,\rm anchor}},
\]

where the same anchor \(R_g\) is used for every candidate of one family/replicate. Thus arbitrary KnotPlot overall scale is removed **once**, while relative Q breathing survives.

Default configs therefore contain:

```json
"scale_normalization_mode": "family_anchor"
```

Legacy `per_candidate` mode is retained only for auditing and should **not** be used for a Q-breathing landscape.

## 3. Consistent reference-basis projection

At the family reference geometry, finite differences construct

\[
T_q=\partial_q\mathbf X,\qquad
T_h=\partial_h\mathbf X,\qquad
T_p=\partial_p\mathbf X.
\]

The same reference basis is transported to every candidate and stripped of the local tangential component. The normal Biot--Savart velocity is then projected through the full Gram system

\[
G_{ij}=\langle T_i,T_j\rangle,
\qquad
b_i=\langle T_i,\mathbf U_\perp\rangle,
\qquad
G\mathbf F=\mathbf b,
\]

with

\[
\mathbf F=(F_q,F_h,F_p)^T.
\]

This is important for the 1-D star sweep: in v0.1.2 an off-axis point could be projected in a 1-D basis while the origin was projected in 3-D, so the resulting coefficients were not directly comparable.

The runner reports both the raw Gram condition number and the scale-free correlation-matrix condition number. The latter is used as the basis-quality gate.

## 4. Fixed point and restoring gates

A local candidate must satisfy

\[
\|\mathbf F\|\approx0.
\]

The local Jacobian is

\[
J_{ij}=\frac{\partial F_i}{\partial \xi_j},
\qquad \boldsymbol\xi=(q,h,p),
\]

and linear restoring stability requires

\[
\boxed{\max_k\Re\lambda_k(J)<0}.
\]

The 1-D star contains enough information for the complete central Jacobian because v0.1.3 evaluates all three \(F\)-components at every Q/H/P axis point in the same reference basis.

A local affine root is estimated by

\[
\boldsymbol\xi_\star
=\boldsymbol\xi_0-J^{-1}\mathbf F_0.
\]

It must remain inside the actual neighboring QHP cell.

## 5. Independent short-time confirmation

The same candidate is evolved with RK4 under the finite-core Biot--Savart dynamics. After rigid/cyclic alignment, the short-time displacement is projected into the **same** reference basis, giving

\[
\mathbf F^{\rm short}.
\]

For a 1-D restoring crossing, v0.1.3 now requires all of the following:

1. instantaneous \(F_\xi\) actually changes sign;
2. its slope is negative;
3. \(F_\xi^{\rm short}\) also actually changes sign in the same bracket;
4. the short-time slope is negative;
5. the instantaneous and short-time roots agree within the configured fraction of the bracket width;
6. instantaneous and short-time projection fractions both pass;
7. the reference basis passes the condition-number gate.

A negative short-time slope **without** a short-time zero crossing is explicitly insufficient.

For a 3-D point, instantaneous and short-time Jacobians are both required to be stable. Instantaneous and short-time affine roots are solved independently and must both lie in the neighboring cell and agree.

## 6. Projection gate

The QHP manifold is only informative if a non-negligible part of the normal dynamics lies inside it. The runner reports

\[
f_{\rm proj}
=\frac{\|\mathbf U_{\rm QHP}\|^2}{\|\mathbf U_\perp\|^2}.
\]

If the entire sampled manifold remains below the configured projection threshold, the result is

```text
INDETERMINATE_WEAK_QHP_MANIFOLD_COUPLING
```

rather than a false PASS or a strong physics FAIL. In that situation the chosen Q/H/P coordinates simply do not span enough of the actual motion.

## 7. Input

Use QHP Sweep Generator v0.1.1 or newer. The sweep root must contain `qhp_metadata.csv` with at least

```csv
file,family,q,h,p,replicate,geometry_ok
knot_6.3/knot_6p3_q0_h0_p0.txt,knot_6.3,0,0,0,0,true
```

v0.1.3 preserves the v0.1.2 metadata-integrity rules:

- `geometry_ok=false` is excluded before physics;
- duplicate geometry file paths are a hard error;
- duplicate `(family, replicate, q, h, p)` nodes are a hard error;
- unique source identities such as `knot_6.3` and `link_6.3.1` remain separate manifolds.

## 8. Runs

Basic:

```bat
run_all.cmd C:\workspace\projects\SST-Workbench\KnotPlot\qhp_6p3
```

Extended + resolution ladder:

```bat
run_all_extended.cmd C:\workspace\projects\SST-Workbench\KnotPlot\qhp_6p3
```

For the full corrected generator dataset:

```bat
run_all_extended.cmd C:\workspace\projects\SST-Workbench\KnotPlot\qhp_extended
```

Important outputs:

```text
outputs\extended\analysis\blind_analysis_summary.json
outputs\extended\analysis\blind_zero_crossings.csv
outputs\extended\analysis\blind_fixed_point_candidates.csv
outputs\extended\analysis\blind_affine_fixed_point_candidates.csv
outputs\RESOLUTION_SUMMARY.json
```

Inspect the blind result before interpreting revealed family names.

## 9. Verdict meanings

- `PASS_CANDIDATE_RESTORING_STRUCTURE` — at least one preregistered restoring candidate survives instantaneous, short-time, projection and basis gates.
- `FAIL_NO_RESTORING_STRUCTURE` — the sampled QHP manifold is sufficiently coupled/resolved but no restoring candidate survives.
- `INDETERMINATE_WEAK_QHP_MANIFOLD_COUPLING` — the QHP coordinates capture too little of the actual normal velocity for a strong conclusion.
- `INDETERMINATE_INSUFFICIENT_GRID` — insufficient finite-difference structure.

A PASS remains a numerical result for the regularized finite-core filament model. It is not proof of a stable 3-D Euler vortex tube and not evidence for SST ontology by itself.

## 10. Windows/MSVC

The native C++17/OpenMP pybind11 kernel is unchanged from v0.1.2 and uses `py::ssize_t`, avoiding the earlier MSVC global-`ssize_t` failure.

## References

```latex
\begin{thebibliography}{99}
\bibitem{Saffman1992}
P. G. Saffman,
\emph{Vortex Dynamics},
Cambridge University Press (1992).

\bibitem{Kabsch1976}
W. Kabsch,
``A solution for the best rotation to relate two sets of vectors,''
\emph{Acta Crystallographica Section A} \textbf{32}, 922--923 (1976).
\end{thebibliography}
```
