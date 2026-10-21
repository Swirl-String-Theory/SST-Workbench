# SmoothClasp Geometry Contract — v0.2.3

**Source family:** TikZ-derived periodic cubic 5_2, 6_1 (14 projected control points; recorded 5_2 P10 regularization), with 3D over/under lifts. The source is not a certified exact numerical realization of Hobby-curves.

## Geometry

For source center `c=(c_x,c_y)` and `R>0`, set

`theta=arg((x-c_x)+i(y-c_y))`, `r=sqrt((x-c_x)^2+(y-c_y)^2)`.

The smooth-clasp map is

\[
\alpha(\theta)=\alpha_0+(\alpha_b-\alpha_0)
\exp\left[\frac{\cos(\theta+\pi/2)-1}{\sigma^2}\right],
\qquad 0<\alpha_0\le\alpha_b.
\]
\[
r'=R+\alpha(\theta)(r-R),\qquad
(x',y',z')=s\bigl(c_x+r'\cos\theta,\;c_y+r'\sin\theta,\;z\bigr),\quad s=30.
\]

All lengths are in arbitrary KnotPlot units; angles in radians. At fixed theta, `dr'/dr=alpha(theta)>0`. The map is an injective, smooth, orientation-preserving ambient deformation of an annular domain avoiding its polar axis. Thus the *continuous source curve* retains its knot type under the map; independently discretized polygonal curves require further isotopy qualification.

The 3D lift is generated from the verified alternating crossing data with a **wider** Gaussian-like profile `width=0.020` in normalized arclength parameter versus `0.011` in v0.2.2. The amplitude remains `0.10` before the scale factor. No physical dynamics is encoded in the lift.

Uniform arclength sampling is obtained by a periodic cubic interpolation followed by rechecking invariants on the sampled polygonal knot. More sampling points alone never prove thick-tube isotopy or smooth motion.

## Gates

- S0: finite coordinates and all required outputs; PASS in local build.
- S1: 5/6 transverse 2D projection crossings, alternating over/under, Alexander coefficients `[2,-3,2]` / `[2,-5,2]`, determinant 7/9; PASS in local build.
- S2: KPT binary roundtrip, exact equality of decoded and supplied coordinate array; PASS.
- S3: finite segment-to-segment nonlocal distance **greater** than `1.1 * close = 0.22` KnotPlot units, with a globally complete midpoint neighborhood exclusion bound; PASS.
- S4: resampled edge-length coefficient of variation <= 0.04; PASS.
- S5: actual KnotPlot `load`, `go 1`, `go 32`, manual checkpoints, and projected collision checks; **NOT EXECUTED** (Windows/KnotPlot required).
- S6: knot-type preservation continuously through relaxations; **UNRESOLVED**. Checkpoint matching Alexander polynomials is not sufficient to certify absence of intermediate reconnections.
- S7: internal-vorticity transport and toroidal rolling driven by finite-core Biot–Savart/Euler dynamics; **NOT EXECUTED**. KnotPlot damping is NOT Euler flow.

The topological data computed are not exhaustive invariants, and the computed curvature is polygonal `turning angle / local edge length`. A converged `go` shape is not automatically a physical vortex state.

## Falsifiable physical hypothesis (future work)

Let `Gamma` be vortex circulation and `X_i(t)` a filament centerline from Euler-consistent finite-core dynamics, not KnotPlot's relaxation time. Define a ring symmetry axis `n` and a circular control of matched hydrodynamic impulse and/or length. Test the measured global ring-orientation rate and internal phase transport against the unknotted control, with `Gamma -> -Gamma` reversing Euler advection signs for an otherwise identical inviscid ideal-fluid setup. A nonzero toroidal rolling rate is not a prior assumption.

**Not a verified physical prediction** until independent vortex dynamics, trajectory controls and mesh/time/core convergence have been executed.

## Bibliography

\bibitem{SchareinKnotPlot} R. G. Scharein, *KnotPlot Manual*, Hypnagogic Software, https://knotplot.com/manual/.
\bibitem{Alexander1928} J. W. Alexander, ``Topological Invariants of Knots and Links,'' *Transactions of the American Mathematical Society* **30**, 275--306 (1928), DOI:10.1090/S0002-9947-1928-1501429-1.
\bibitem{Conway1970} J. H. Conway, ``An Enumeration of Knots and Links, and Some of Their Algebraic Properties,'' *Computational Problems in Abstract Algebra*, Pergamon (1970), DOI:10.1016/B978-0-08-012975-4.50034-5.
