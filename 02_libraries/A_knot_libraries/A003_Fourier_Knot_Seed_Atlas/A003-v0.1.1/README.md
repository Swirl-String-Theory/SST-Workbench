# SST Fourier Knot Seed Atlas v0.1.1

**Status: GEOMETRIC_SEEDS_ONLY — NOT PKLSA-QUALIFIED.**

Contains deterministic analytical knot centerline parameterizations in `generate.py`, and sampled dimensionless `x y z` files under `xyz/` with no headers (one point per line, periodic closure implicit; the closing point is deliberately not duplicated). `manifest.json` records origin, representation, sha256, sampling, and discrete perimeter.

Run: `python generate.py` (requires NumPy; defaults to BASIC and FULL).

## Resolution profiles

| Profile | Points per closed curve | Purpose |
|---|---|---|
| BASIC | 1200, 2400 | Baseline seed generation and initial spatial convergence |
| FULL | 4800, 9600 | Higher-resolution geometric seed and spatial convergence checks |

Use `python generate.py --profiles BASIC` or `python generate.py --profiles FULL` to generate one profile; alternatively `python generate.py --points 1200 2400 4800 9600`.

The `xyz/` paths and filenames for BASIC are **unchanged from v0.1.0**; `N4800` and `N9600` entries are added to the same folder. Both `manifest.json` and `manifest.csv` include a `profile` field. Each point resolution contains both `uniform_t` and `uniform_s_polyline` exports for every analytic seed. No duplicate endpoint is written. Both profiles contain geometry only: `FULL` is **not** a PKLSA-certification status. Generated counts: 30 seeds x 4 resolutions x 2 sampling modes = **240 XYZ files**.


## Mathematical definitions

For $0<t<2\pi$ and coprime $1<p<q$:

- Torus direct: $((2+\cos qt)\cos pt,(2+\cos qt)\sin pt,\sin qt)$.
- Hoste minimal: $(\cos pt,\cos(qt+\pi/2p),-\sin pt+\cos((q-p)t+\pi/2p-\pi/4q))$.

Twist knot diagrams $K_m$ have $m$ twist half-crossings plus a clasp with two crossings; Rolfsen names up to $m=8$: $3_1,4_1,5_2,6_1,7_2,8_1,9_2,10_1$.

Boocher et al. Thm 5.5 for even $m=2n\geq2$:

- $x=\cos2t$,
- $y=\cos((2n+1)t+1/2)$,
- $z=\cos(2t+\pi/4)+\cos((2n+3)t+(2n+3-3\pi)/(2(2n+1)))$.

For $m=4n+1\geq5$:

- $x=\cos2t$,
- $y=\cos((8n+3)t+1/2)$,
- $z=\cos(2t+\pi/4)+\cos((8n+1)t+(8n+1+(8n+5)\pi)/(2(8n+3)))$.

Hoste & Zirbel Thm 4: a Lissajous family indexed by $k\geq0$:

- $x=\cos2t$,
- $y=\cos((2k+1)t+1/2)$,
- $z=\cos((6k+7)t+(6k+7-3\pi)/(4k+2))$.

This gives $K_{2k}$ if $k$ even, and the **mirror** of $K_{2(k+1)}$ if $k$ odd. The latter is the mirror of $K_{4n+3}$ when $k=2n+1$, using $K_m \sim$ mirror of $K_{-m-1}$ per knot diagram conventions.

Kauffman 1997 special seeds:
- $3_1$: $(\cos2t,\cos(3t+1/2),\tfrac12\cos(5t+1/2)+\tfrac12\sin(3t+1/2))$.
- $4_1$: $(\cos t+\cos3t,0.6\sin t+\sin3t,0.4\sin3t-\sin6t)$.

## Validation requirements

- Original equations are exact finite Fourier series and literature-backed up to mirror convention.
- XYZ discretizations are approximations only; check convergence in N, embedding/no self-crossings, signed chirality, and independent knot invariant identification before committing to a validated atlas.
- `uniform_s_polyline` samples piecewise-linearly by estimated cumulative arclength. It is **not** a geometric relaxation or an exact analytic arclength reparameterization.
- Absolute circulation/helicity signs must be specified separately. Mirroring a curve is not equivalent to reversing the order of vertices.
- Never infer dynamical Euler/PKLSA stability from the Fourier representation or from ropelength optimality.
- A physical unit conversion, if ever intended, must be documented as an additional independent modeling assumption.

## Sources

1. L. H. Kauffman (1997), *Fourier Knots*, arXiv:q-alg/9711013 (Sections 4, 5, 7), https://arxiv.org/pdf/q-alg/9711013
2. J. Hoste (2009), *Torus knots are Fourier-(1,1,2) knots*, *Journal of Knot Theory and Its Ramifications* **18**(2), 265–270. DOI:10.1142/S0218216509006926, arXiv:0708.3590.
3. A. Boocher, J. Daigle, J. Hoste, W. Zheng (2009), *Sampling Lissajous and Fourier Knots*, *Experimental Mathematics* **18**(4), 481–497. DOI:10.1080/10586458.2009.10129057 (Theorem 5.5).
4. J. Hoste, L. Zirbel (2007), *Lissajous Knots and Knots with Lissajous Projections*, *Kobe Journal of Mathematics* **24**(2), 87–106. DOI:10.24546/E0034450 (Theorem 4).
