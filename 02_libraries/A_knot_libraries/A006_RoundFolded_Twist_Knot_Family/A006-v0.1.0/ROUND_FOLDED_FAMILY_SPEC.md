# RoundFolded Twist Knot Family (proposed PKLSA geometry convention)

**Version:** 0.1.0 • **Scientific status:** `STATIC_CANDIDATE_ONLY` • **Not an SST physical canon or a validated Euler solution.**

## 1. Topological family (source-independent definition)

Let \(m\in\mathbb N,\;m\ge1\) be the number of signed half-twists in a rational tangle, with the clasp fixed by the Conway presentation

$$
T_m\equiv C(m,2),\qquad \frac{p}{q}=[m,2]=m+\frac12=\frac{2m+1}{2}.
$$

The mirror chirality depends on crossing convention. This is the **topological** definition of the intended twist-knot family, not a formula for the Euclidean 3D embedding. KnotPlot's `conway {m}2` is provided as a *runtime acquisition candidate*; validate its exact Conway parser on the installed executable before treating the output as authoritative.

| m | twist knot | Conway | expected crossing number | expected determinant |
|--:|:--|:--|--:|--:|
| 1 | 3_1 | [1,2] | 3 | 3 |
| 2 | 4_1 | [2,2] | 4 | 5 |
| 3 | 5_2 | [3,2] | 5 | 7 |
| 4 | 6_1 | [4,2] | 6 | 9 |
| 5 | 7_2 | [5,2] | 7 | 11 |
| 6 | 8_1 | [6,2] | 8 | 13 |

The normalized Alexander polynomial targets (up to \(\pm t^k\)) are:

$$
\Delta_m(t)=\begin{cases}
\frac{m+1}{2}(t+t^{-1})-m,&m\text{ odd},\\
-\frac{m}{2}(t+t^{-1})+(m+1),&m\text{ even}.
\end{cases}
\quad\Rightarrow\quad\det(T_m)=|\Delta_m(-1)|=2m+1.
$$

These are **target invariants**; they are NOT calculated from the generated XYZ embeddings in this release.

## 2. One common constructive 3D embedding rule

Given a closed polygonal realization \(K_m:S^1\to\mathbb R^3\) of the specified twist knot (with immutable provider hash), start with the nearly circular carrier

$$
\mathbf C_R(\theta)=(R\cos\theta,R\sin\theta,0).
$$

Choose a short carrier arc \(I\) and a nondegenerate source edge \(e_m\). Delete those arcs/edges, use the cut source open polygon \(K_m\setminus e_m\), and reconnect in order using two cubic Hermite branches \(H_L,H_R\):

$$
\boxed{\;
X_m=\operatorname{close}\left[\mathbf C_R|_{S^1\setminus I}\;\Vert\;H_L\;\Vert\;\mathcal A_{\eta,\lambda}(K_m\setminus e_m)\;\Vert\;H_R\right].\;}
$$

Here the anisotropic, *invertible* local fold is

$$
\mathcal A_{\eta,\lambda}(\mathbf q)
=\mathbf p_0+\lambda\left[\mathbf t\mathbf t^\top
+\eta(I-\mathbf t\mathbf t^\top)\right]Q(\mathbf q-\mathbf q_0),
\quad 0<\eta\le1,\;\lambda>0,
$$

with \(\mathbf t\) the attachment tangent, \(Q\in SO(3)\), and \(\eta\) the fold/compression ratio. The implementation uses piecewise-polynomial Hermite bridges, smooth radial-shoulder corrections, and closed arclength resampling. It records the source-cut edge and source hash.

**Limitation:** even with a non-singular local affine map, the two reconnecting arcs and resampling can alter ambient isotopy. A topological certificate must check component knot types before promotion. It is incorrect to claim that a localized sinusoid alone proves the desired twist-knot family.

## 3. Small distance between doubled ropes

Let \(d_*(X_m)\) be the *nonlocal* minimal segment-to-segment centerline distance (excluding four adjacent beads on each side), \(a\) be the chosen tube radius, and \(\delta\) a clearance margin:

$$
\boxed{d_*\ge2a+\delta>0.}
$$

The user-desired 'almost touching folded rope' is a **dimensionless relative shape goal**, \((d_*-2a)/R\ll1\), **not** zero centerline clearance. In this release `fold_ratio=0.8` compresses transverse directions of the local knot and an independent global scale factor `7.0` makes its sampling safer relative to KnotPlot's `close` threshold. Neither \(a\) nor the physical SST core radius is calibrated; no numerical SST material claim follows from these units.

## 4. Borromean carrier and insertion

The base link is the closure of the three-strand braid

$$
\beta_B=(\sigma_1\sigma_2^{-1})^3.
$$

Three **locally knotted** connected-sum candidates are created by the same decoration operation, at separated braid sectors. Standard preset:

$$
\boxed{B(T_3,T_3,T_4)=B(5_2,5_2,6_1).}
$$

Each decorated component is **intended** to carry its local twist-knot type, and the base retains a Borromean structural design. However, pairwise linking numbers \(Lk_{ij}=0\) are not a certificate for the Borromean triple invariant \(\bar\mu_{123}\), nor do they certify all proper sublinks or knot summands. An independent 3D isotopy/PD/Jones/Alexander gate is required. The component sources `5_2` are the *same* provider (not independent experimental replicates).

## 5. Numerical qualification and blocking gates

- G0 Source hash and precise provider representation: **PASS** for bundled 300-vertex snapshot inputs, other m requiring acquisition.
- G1 KPT LOCD roundtrip and component count: **PASS** in local Python.
- G2 Closed-curve positive nonlocal self-clearance and intercomponent clearance \(>0.12\) in **KnotPlot coordinate units**: **PASS** for the included BASIC and FULL outputs; not sufficient for topology safety during go.
- G3 Edge-length uniformity after arclength remeshing: **PASS** by static metrics.
- G4 Independent component knot polynomial / source-to-target isotopy: **UNRESOLVED**.
- G5 Independent triple Milnor invariant and proper sublink checks: **UNRESOLVED**.
- G6 Actual KnotPlot `load`, `go` and collision monitoring on user's installed version: **NOT TESTED**.
- G7 Euler finite-core vorticity/pressure initialization, energy/helicity/circulation conservation and convergence: **NOT TESTED**.

Do not promote outputs into E010/E011 `STATIC_READY` until G4, G5 are independently satisfied. Old relaxed KnotPlot snapshots are immutable **input candidates**, not physical empirical ground truth. The generator does NOT run `go` automatically.

## 6. Provenance, launch, and commands

From an extracted copy of this package on Windows (NumPy + SciPy installed):

```bat
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd BORROMEAN
run_all.cmd ACQUIRE
```

Alternatively:

```bat
py -3 src\build.py --mode INDIVIDUAL --m 3 4 5 6 --n 256
py -3 src\build.py --mode BORROMEAN --borromean-m 3 5 6 --n 256
```

From KnotPlot command window, while the project's root is the working directory:

```text
read output/individual/Tm3_5_2_N0256/Tm3_5_2_N0256_LOAD.kpc
read output/borromean/Borromean_5_2_5_2_6_1_N0256/Borromean_5_2_5_2_6_1_N0256_LOAD.kpc
```

Use the respective `_GO1.kpc` only after checking for adequate clearance. For m>6: use `read acquisition/acquire_Tm7.kpc` as a *KnotPlot-local proposal*, check the result matches Conway `[7,2]` and the determinant target, then rebuild with `--m 7`. If KnotPlot does not accept the proposed `conway 72` syntax, that acquisition lane is blocked pending version-specific syntax correction; other builds remain valid.

Folder suggestion: `02_libraries/A_knot_libraries/_staging/RoundFolded_Twist_Knot_Family_v0.1.0` until registry ID allocation.

## 7. References (copy-ready LaTeX)

```latex
\bibitem{Conway1970}
J. H. Conway, ``An Enumeration of Knots and Links, and Some of Their
Algebraic Properties,'' in \emph{Computational Problems in Abstract Algebra},
Pergamon (1970), pp.~329--358.
\href{https://doi.org/10.1016/B978-0-08-012975-4.50034-5}{doi:10.1016/B978-0-08-012975-4.50034-5}.

\bibitem{SchareinKnotPlotManual}
R. G. Scharein, \emph{KnotPlot Manual}, Hypnagogic Software (1996--present),
\url{https://knotplot.com/manual/commands.html}.

\bibitem{KnotAtlas}
D. Bar-Natan et al., \emph{The Knot Atlas}, University of Toronto,
\url{https://katlas.org/}.
```