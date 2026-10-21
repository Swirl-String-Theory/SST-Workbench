# RoundFolded Twist Knot Family v0.2.1 — TikZ-control-point reconstruction

**Status: DEVELOPMENT / STATIC_CANDIDATE.** This is a targeted source-anchored repair of the v0.2.0 visually incorrect 4-plat-to-annulus map. Previous versions remain immutable. No physical Euler/PKLSA dynamics certification.

## What is actually produced

- Individual **5_2** and **6_1** from the user's 14 ordered TikZ `P1`–`P14` coordinates, each as one continuous closed loop.
- A periodic **cubic-spline surrogate**, *not mathematically identical* to TikZ's Hobby interpolant; the exact source control points are saved in source code and reports.
- Automatic search of transverse crossings in the resulting 2D projection, alternating over/under assignment, then localized smooth 3D lifts; 5_2 has 5 crossings / Alexander polynomial `2t²−3t+2`, 6_1 has 6 / `2t²−5t+2`.
- 5_2 source places P3 and P10 at exactly `(0,2)`; P10 is raised by 0.07 in Y for a nondegenerate planar projection. This is transparent and must be revalidated if modified.
- `output/borromean/Borromean_skeleton_ONLY/`: three-component Borromean *reference skeleton*, **not** a composed 5_2+5_2+6_1 geometry.
- `.xyz`, `.kpt`, `.kpc`, per-case `REPORT.json`, tests and preview.

## Commands from Windows Command Prompt

```cmd
py -3 -m pip install -r requirements.txt
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd FULL
```

SMOKE = 256 beads/individual; BASIC = 512; FULL = 1024. The fixed nominal scale is 12.0 arbitrary KnotPlot length units, physically dimensionless. No slider is silently changed. KnotPlot's numerical `close` must be re-probed on the actual workstation rather than inferred from this package.

Open KnotPlot with the unpacked project root as working directory:

```text
read output/individual/TikZRoundFold_5_2_N0512/TikZRoundFold_5_2_N0512_LOAD.kpc
read output/individual/TikZRoundFold_6_1_N0512/TikZRoundFold_6_1_N0512_LOAD.kpc
read output/borromean/Borromean_skeleton_ONLY/Borromean_skeleton_ONLY_LOAD.kpc
```

**Important:** the second load resets KnotPlot, so view each one separately.

For a dynamics check **after loading only one geometry**:

```text
read output/individual/TikZRoundFold_5_2_N0512/TikZRoundFold_5_2_N0512_GO1.kpc
```

After the step actually completes, take a separate snapshot using the corresponding `_SNAPSHOT.kpc`. Never run automatic `go 32` plus snapshot together without checking KnotPlot's asynchronous execution status.

## Scientific constraints

The diagrams' expected polynomials and determinants agree with twist knots, but projection equivalence to the exact user-compiled TikZ Hobby curves is **not formally established**. Static shortest-segment screens are discrete-polyline approximations, and they cannot guarantee ambient-isotopy preservation under KnotPlot relaxation. Source `flip crossing/.list` is not translated directly because numeric crossing IDs depend on the TikZ knot-diagram runtime; alternating assignment is explicitly registered instead. For a strict source-faithful implementation, extract the actual Hobby cubic Bézier controls from the compiled TikZ path and the resolved knot crossing registry.

**Borromean decoration is deliberately blocked** until local splicing is replaced with a verified integrated three-component projection, including component invariants and a Milnor triple-link certificate. Avoid further reproducing the rejected `ring + knotblob` appearance.
