# RoundFolded Near-Unknot v0.2.2 (individual twist-knot builds)

**Development / geometry-only / not physically certified.**

This is a versioned *extension* of `RoundFolded_Twist_Knot_Family_v0.2.1_TIKZ`, retaining its 14-point TikZ-derived spline inputs and its reconstructed alternating crossings. It generates **individual** near-circular `5_2` and `6_1` variants, not a Borromean link. Neither original v0.2.1 outputs nor frozen falsifiers are modified.

## Design and explicit geometry

For projected polar coordinates \((r,\theta)\) about the bounding-box center \(\mathbf c\), apply

$$
  F_{\alpha,s}(r,\theta,z)=
  \bigl(s[R+\alpha(r-R)]\cos\theta,\;
        s[R+\alpha(r-R)]\sin\theta,\;sz\bigr),\quad 0<\alpha\le1,\;s>0,
$$

with the xy center re-added before scaling, and \(R\) the median source radius. This is an injective ambient map on the annulus occupied by the continuous source curve, provided the whole radial image stays positive. In combination with a continuous change of \(\alpha\), it gives an explicit ambient isotopy of the *smooth source geometry*, not a proof of topology preservation for the independently resampled straight-line polygonal export.

| Profile | Radial squeeze alpha | Global scale s | Suggested visual KnotPlot `cyl-rad` |
| --- | ---: | ---: | ---: |
| ROUND | 0.42 | 1.50 | 0.12 |
| TOROIDAL | 0.23 | 2.00 | 0.09 |
| NEAR_UNKNOT | 0.12 | 2.50 | 0.06 |

The profile scale and subsequent factor 12 are *numerical display/export scales*; they are **not** SST's physical vortex core radius. Visual radius (`cyl-rad`) is a renderer setting and independent of physical finite-core vorticity. In the `.kpc` files it is only queried; the suggested setting is **not automatically applied**. The KnotPlot `close` parameter must be checked on the machine where `go` is run.

## Installation and usage (Windows, from the extracted project root)

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd FULL
```

Modes use 256, 512 and 1024 equally spaced points per closed component, respectively. Each mode generates both 5_2 and 6_1 in the three shape profiles plus two matched-unknot controls (major radius and total length). Each case has XYZ/KPT/KPC outputs and a JSON report.

Example KnotPlot commands (working directory = this project's root):

```
read output/individual/NearUnknot_5_2_NEAR_UNKNOT_N0256/NearUnknot_5_2_NEAR_UNKNOT_N0256_LOAD.kpc
read output/individual/NearUnknot_5_2_NEAR_UNKNOT_N0256/NearUnknot_5_2_NEAR_UNKNOT_N0256_GO1.kpc

read output/individual/NearUnknot_5_2_NEAR_UNKNOT_N0512/NearUnknot_5_2_NEAR_UNKNOT_N0512_LOAD.kpc
read output/individual/NearUnknot_5_2_NEAR_UNKNOT_N0512/NearUnknot_5_2_NEAR_UNKNOT_N0512_GO1.kpc
```

Record the snapshot **only after KnotPlot completes** its iterations:

```
read output/individual/NearUnknot_5_2_NEAR_UNKNOT_N0512/NearUnknot_5_2_NEAR_UNKNOT_N0512_SNAPSHOT.kpc
```

Never assume returning from `go` means an asynchronous GUI iteration has finished; verify via runtime/log/snapshot. Run first on `SMOKE` and back up the original seeds before any long relaxation.

## Static checks and physical questions

- Crossings and Alexander polynomial of the **generated 3D embedding** are recomputed from its xy projection. Expected: `5_2`: 5 crossings, polynomial `[2,-3,2]`, determinant 7; `6_1`: 6 crossings, polynomial `[2,-5,2]`, determinant 9. A matching polynomial is a **necessary but not sufficient** knot-type certificate.
- Check numerically non-adjacent line segment clearance for each output and KPT binary roundtrip, plus optional uniform arc-length convergence. These tests do **not** prove no crossing during `go` or ambient isotopy of the polygonal resampling.
- The projection's **signed polar winding number around the central hole equals zero** for both cases. It is **not** the +1 major-axis winding of a simple oriented ring. Therefore, visually circular shape must not be promoted into an assertion of ring-like hydrodynamic impulse or self-propulsion.
- `REPORT.json` gives a *geometric impulse factor* `area_vector = (1/2) sum(X_i cross X_{i+1})`, normalized by `pi R^2`. For a thin vortex filament with common circulation Gamma and density rho, the impulse is \(\mathbf I=\rho\Gamma\mathbf A\). This is only a **conditional** filament-model proxy, not a measured PKLSA velocity.
- **No Euler time integration, core model, source-native PKLSA simulation, independent topological recognizer, Milnor invariant, or dynamical stability certification has been run.**

## Target-free toroidal-roll falsifier (future work)

For each knot and matched unknot, use the identical signed circulation \(\Gamma\), finite-core profile \(a\), and matched absolute `dt/(R^2/Gamma)` with native PKLSA/Euler solver. Compare reversing Gamma and mirroring the embedding. Distinguish translations, rigid-body rotations, marker motion along the major ring, and poloidal phase rotation about a torus's tube. Measure independent observables: center-of-vorticity, impulse, energy, arclength, geometric major-axis/poloidal phase, and self-intersection/reconnection; perform convergence in spatial/temporal resolutions and core radius. 'Roll' is a predicted phenomenon to falsify, **not** a consequence of the shape transform.

Use the scale \(t_\Gamma=R^2/|\Gamma|\) (units seconds) and dimensionless time \(t/t_\Gamma\). A non-zero drift speed, if observed, is reported as \(U R/|\Gamma|\) and separately from internal phase frequency \(\Omega R^2/|\Gamma|\).

## Status

`GEOMETRY_STATIC_CANDIDATE`; not `STATIC_READY`, not `PKLSA_DYNAMIC_QUALIFIED`. This package only produces *individual* knots. Do not use it to certify decorated Borromean links.

## References

```latex
\bibitem{Alexander1928}
J.~W. Alexander, ``Topological Invariants of Knots and Links,''
Transactions of the American Mathematical Society 30, 275--306 (1928),
\url{https://doi.org/10.1090/S0002-9947-1928-1501429-1}.

\bibitem{Saffman1992}
P.~G. Saffman, \emph{Vortex Dynamics}, Cambridge University Press (1992),
\url{https://doi.org/10.1017/CBO9780511624063}.

\bibitem{Kabsch1976}
W. Kabsch, ``A solution for the best rotation to relate two sets of vectors,''
Acta Crystallographica A 32, 922--923 (1976),
\url{https://doi.org/10.1107/S0567739476001873}.
```