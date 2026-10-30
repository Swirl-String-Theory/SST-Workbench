# PKLSA Borromean 5_2 + 5_2 + 6_1 — Go diagnostics v0.1.1

**Status: STATIC_DIAGNOSTIC_CANDIDATE_ONLY.** New, non-certified release; v0.1.0 remains unchanged. Finite-core Euler, pressure, Biot–Savart dynamics and complete link-knot certifications are **NOT** included.

## Why this patch

v0.1.0 embeds an assembled three-component decorated Borromean-skeleton link at 3321 beads with long, highly kinked knot/bridge junctions. Its KPC loader does not perform `go`. In KnotPlot, `go niter` runs **KnotPlot's knot-length relaxation**, not Euler evolution. A GUI button may look inert while large collision-avoiding geometry takes considerable time; the issue must be isolated from the geometry.

v0.1.1 prepares two *new* reduced, less vertically separated candidate geometries using a braid carrier of radius 8 (was 13), knot altitude 1.55 (was 4.8), and a Hermite blending at the outer ring attachment (sharp turns **remain** near the knot splice). SMOKE (921 beads) and BASIC (1851 beads). Values are **not slider-optimized scientific parameters**. No source coordinates were changed: the unmodified source files are bundled and SHA256 tracked; the SMOKE tier is resampled, which requires independent topology check.

## KnotPlot: diagnostic sequence (from extracted project root)

First **prove the KnotPlot go mechanism works on a simple control**:

```
read diagnostic/00_solver_trefoil_smoke.kpc
```

This resets default parameters, loads `torus 2 3 128`, exports before, executes `go 1`, and exports after. To compute a displacement after KnotPlot returns:

```
py -3 diagnostic/check_step.py diagnostic/solver_trefoil_before.xyz diagnostic/solver_trefoil_after1.xyz
```

If that works, test **the small composite**:

```
read diagnostic/01_borromean_SMOKE_go1.kpc
```

Then compare:

```
py -3 diagnostic/check_step.py diagnostic/borromean_SMOKE_before.xyz diagnostic/borromean_SMOKE_after1.xyz
```

Only after verifying SMOKE `go 1`, try the larger BASIC geometry:

```
read diagnostic/02_borromean_BASIC_go1.kpc
```

Compare its before/after coordinates analogously. Do **not** immediately run 8192+ iterations. Avoid disabling collisions to get a pretty shape: KnotPlot collisions change knot/link topology and do not qualify a PKLSA seed. Experimental comparison at equal iterations must not be interpreted as physical vortex stability.

`read diagnostic/03_borromean_SMOKE_go32.kpc` is an optional short visual follow-up **only** if `go 1` behaves.

To just view without changing the geometry:

```
read borromean_SMOKE_load_only.kpc
read borromean_BASIC_load_only.kpc
```

## Scientific caveats

- The carrier is modeled as closure of 3-braid `(sigma_1 sigma_2^-1)^3`; the three resulting components contain *intended* local knots of types 5_2, 5_2, 6_1.
- Pairwise Gauss linking integrals are numerically near zero. **This does not prove the triple Borromean invariant or splitness of every proper sublink.** Independently certify isotopy and component knot polynomials before acceptance in E010/E011.
- Radius and coordinate units are dimensionless; no choice of SST physical core radius.
- The `SMOKE` knot contours are resampled from their source polylines. Even with positive sampled clearances, isotopy is not independently verified.
- Each candidate still has sharp local source-to-bridge joins (maximum turning angle above 110 degrees). It is a **diagnostic workaround**, not certified smooth, collision-safe production geometry. The next geometry upgrade must achieve isotopy-certified, finite-core-consistent tangent blending.
- Nothing here establishes why the original `go` appears still; use the before/after test to identify it on the actual executable.

## Rebuild

Python 3.10+, `numpy`, `scipy`. From the extracted project directory: `run_all.cmd`. It regenerates the candidates and runs the Python static tests. The `.kpc` runtime diagnostics require KnotPlot itself.

Primary source geometry: `5_2__knotplot_final.txt`, `6_1__knotplot_final.txt` from the previously verified Drive source snapshots. The second 5_2 is not an independent provider.
