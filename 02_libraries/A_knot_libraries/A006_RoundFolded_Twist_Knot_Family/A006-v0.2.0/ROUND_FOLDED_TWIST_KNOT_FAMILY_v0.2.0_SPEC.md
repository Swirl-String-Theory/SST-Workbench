# RoundFolded Twist Knot Family v0.2.0 — revised mathematical & engineering spec

**Science status: DEVELOPMENT / STATIC_CANDIDATE.**

## 1. Topological presentation

Use the 4-plat closure of the four-strand braid word

\[
\boxed{W_m=\sigma_2^{m}\sigma_1^{-1}\sigma_2,\quad m\in\mathbb{Z}_{\ge1}.}
\]

There are \(m+2\) designated 2D crossings and one closed strand, with the plat closure identifying endpoint pairs \((0,1)\) and \((2,3)\) on both sides. The implemented convention gives:

| m | Intended Rolfsen knot | Crossings | Alexander polynomial in normalized \(t\) | determinant |
|---:|---|---:|---|---:|
| 1 | 3_1 | 3 | \(t^2-t+1\) | 3 |
| 2 | 4_1 | 4 | \(t^2-3t+1\) | 5 |
| 3 | 5_2 | 5 | \(2t^2-3t+2\) | 7 |
| 4 | 6_1 | 6 | \(2t^2-5t+2\) | 9 |
| 5 | 7_2 | 7 | \(3t^2-5t+3\) | 11 |
| 6 | 8_1 | 8 | \(3t^2-7t+3\) | 13 |

The general normalized polynomial is

\[
\Delta_m(t)=k t^2 - (2k+(-1)^m)t + k, \quad k=\lceil m/2\rceil.
\]

**Careful:** The sign convention for Conway entries depends on the chosen rational-tangle closure. The code's actual source of truth is the explicit braid word and plat pairings, not an ambiguous bare string `C(m,2)`.

## 2. Projection-first planar geometry

Four initial braid lanes are \(y_j=(j-\tfrac32)d_b\), \(j=0,1,2,3\), with \(d_b>0\). At each elementary braid crossing exchanging slots \(j,j+1\), parameter \(u\in[0,1]\) uses the \(C^2\) transition

\[
h(u)=6u^5-15u^4+10u^3, \quad
 y_j(u)=(1-h(u))y_j+h(u)y_{j+1},\quad
 y_{j+1}(u)=(1-h(u))y_{j+1}+h(u)y_j.
\]

The crossing lift on the two participating strands is

\[
z_\pm(u)=\pm\sigma H\sin^2(\pi u),\qquad \sigma=\pm1,
\]

with the overpassing strand selected by braid-generator sign. \(H\) is in *dimensionless coordinate units*. Plat closures are semicircular caps attached to the four ends. This produces a closed 3D polygon, with no knot `blob` inserted onto a ring.

## 3. Round folded annular map

The 4-plat rectangle \((x,y)\) is embedded into an annular sector via

\[
\boxed{\mathbf X_m(x,y,z)=((R+y)\cos\Theta_m(x),\; (R+y)\sin\Theta_m(x),\; z).}
\]

The angle map \(\Theta_m(x)\) is strictly increasing (shape-preserving PCHIP): twist crossings are clustered in the upper sector; two clasp crossings are placed near the lower sector; all four plat lanes follow nearly the same large circular carrier. We require \(R+\min y>0\) and angular range strictly less than \(2\pi\); these guarantee the 2D coordinate map is injective on the braid-and-cap strip before discretization. The values of \(\Theta_m\) are specified in `src/roundfold.py` rather than inferred from screenshots.

**Geometry of close double passes:** the adjacent lane spacing \(d_b/R\) controls the relative separation between strands. At defaults \(d_b/R = 0.48/17 \approx 0.02824\). This ratio can be reduced subject to 3D-clearance and sampling gates; *zero spacing is never permitted*. For a prospective filament tube radius \(a\), true finite-core non-contact would require \(d_{\rm centre}\ge2a(1+\epsilon)\), a separate hypothesis that cannot be concluded from a 2D projection. The source's canonical SST \(r_c\) is **not** being assigned to these dimensionless KnotPlot geometries.

## 4. Resolution, source and handedness

Arclength resampling occurs only after constructing the complete 3D curve, with *no duplicated closing bead*. N = 512 is a diagnostic preview; BASIC N = 1024 and FULL N = 2048 are the initial study levels for individual knots. Mirror symmetry is obtained from \(z\mapsto-z\) but it must also be independently checked in KnotPlot where relevant. Raw `.xyz` uses three FP64 ASCII columns, `.kpt` uses KnotPlot 1.0 LOCD binary, and `.kpc` loads the `.kpt`.

## 5. Borromean decorated composite

The unknotted Borromean **skeleton** is the closure of the 3-braid \((\sigma_1\sigma_2^{-1})^3\). The current v0.2.0 composition performs three geometric local splices with projection-first \(T_m\) source curves into the skeleton components. A successful local connected sum should preserve the underlying inter-component Brunnian entanglement, but only *provided* the local-splice insertion ball is certified disjoint and topologically valid. That certificate has **not** yet been established. Neither approximate pairwise linking 0 nor the KPT shape constitutes proof of \(\bar\mu_{123}=\pm1\).

In particular **the individual algorithm is fully revised, but Borromean uses a provisional, local-splice adapter**. An integrated no-blob three-component projection-first carrier remains a development objective rather than an achievement of v0.2.0.

## 6. Qualification gates and stopping rules

| Gate | Test | status at successful local build |
|---|---|---|
| G0 | Code generation, reproducible deterministic seed and file manifest | PASS |
| G1 | One component per individual 4-plat | PASS |
| G2 | Fox/Alexander invariant for each theoretical braid diagram | PASS |
| G3 | Sampled 2D intersection count and nonzero 3D over/under lift | PASS |
| G4 | Sampled geometric clearance screening and KPT binary roundtrip | PASS_SCREEN |
| G5 | KnotPlot reimport + one-step asynchronous completion | NOT_TESTED |
| G6 | Knot type after independent KnotPlot import, smoothing, resampling & relaxation | UNRESOLVED |
| G7 | Borromean source-native local-ball/isotopy certificate | UNRESOLVED |
| G8 | Milnor \(\bar\mu_{123}\) or other independent triple-link classifier | UNRESOLVED |
| G9 | Mesh/time/core convergence and Euler finite-core dynamics | NOT_TESTED |

**The braid-diagram invariants are not independent evidence that arbitrary polygonal relaxation has retained its knot type.** The KD-neighbor segment-distance screen does not calculate global reach or thickness; it is a development safety screen only. KnotPlot's `go` is a visualization/relaxation computation, not an incompressible Euler solver.

## 7. Minimal next experiment

1. Load \(5_2\) and \(6_1\) BASIC in KnotPlot, capture orthogonal 2D and 3D views.
2. Acquire `parameters` dumps; execute separately a `go 1`, save after completion, then 32 matched steps and save again.
3. Compare invariant crossing sequence before/after. Require no evidence of segment passage; inspect suspicious close-contact intervals.
4. For Borromean, implement genuine certified local-ball surgery and independently compute/verify the triple linking before `STATIC_READY`.

## References (copy-ready LaTeX)

```latex
\bibitem{Conway1970}
J. H. Conway, ``An Enumeration of Knots and Links, and Some of Their
Algebraic Properties,'' in Computational Problems in Abstract Algebra,
Pergamon Press (1970), pp. 329--358.
https://doi.org/10.1016/B978-0-08-012975-4.50034-5.

\bibitem{Alexander1928}
J. W. Alexander, ``Topological Invariants of Knots and Links,''
Transactions of the American Mathematical Society 30, 275--306 (1928).
https://doi.org/10.1090/S0002-9947-1928-1501429-1.

\bibitem{Milnor1954}
J. Milnor, ``Link Groups,'' Annals of Mathematics 59, 177--195 (1954).
https://doi.org/10.2307/1969685.

\bibitem{SchareinKnotPlot}
R. G. Scharein, KnotPlot Manual, Hypnagogic Software,
https://knotplot.com/manual/.
```
