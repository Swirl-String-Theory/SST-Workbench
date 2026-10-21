# RoundFolded Twist Knot Family v0.2.0 — DEVELOPMENT

## What changed vs v0.1.0

**NEW for individual knots:** A deterministic four-strand *plat* projection with rounded global carrier and explicit 3D over/under lifts. This is **not** the v0.1.0 pattern of attaching a separate old KnotPlot knot to a circle. All four source-native KnotPlot exports from v0.1.0 are deliberately absent from the geometry generation step; they may be used only later as independent morphology/comparison references.

**Borromean preview:** Based on the Borromean 3-braid skeleton, with three local **connected-sum candidates** using the new analytic 4-plat knots. This Borromean module still uses local splicing, not the fully integrated projection-first multi-component construction requested as a final target. Its topological and dynamic status is **UNRESOLVED**.

## Windows setup

Use Python 3.10+ in the existing Workbench environment:

```bat
py -3 -m pip install -r requirements.txt
run_all.cmd SMOKE
run_all.cmd BASIC
run_all.cmd FULL
```

- SMOKE: individual 5_2 and 6_1, 512 vertices per component (diagnostic only).
- BASIC: 5_2, 6_1, 7_2, 8_1 at **1024 vertices** each; Borromean 5_2+5_2+6_1 at **768 vertices per component**.
- FULL: 2048 vertices per individual component; 1536 per Borromean component.

Smaller N was rejected as the universal default because the compact double-pass sections require adequate spatial sampling. None of these N-values alone demonstrates numerical convergence.

### Build an arbitrary family member

```bat
py -3 src\build.py --mode INDIVIDUAL --m 3 4 5 6 --n 1024
py -3 src\build.py --mode BORROMEAN --borromean-m 3 4 5 --borromean-n 768
```

## KnotPlot loading

Open KnotPlot with this project directory as its working directory, then:

```text
read output/individual/Tm3_5_2_original_N1024/Tm3_5_2_original_N1024_LOAD.kpc
```

Another standalone case:

```text
read output/individual/Tm4_6_1_original_N1024/Tm4_6_1_original_N1024_LOAD.kpc
```

Borromean development case:

```text
read output/borromean/Borromean_5_2_5_2_6_1_N0768/Borromean_5_2_5_2_6_1_N0768_LOAD.kpc
```

The `*_LOAD.kpc` resets and loads only. To diagnose motion, **after** loading:

```text
read output/individual/Tm3_5_2_original_N1024/Tm3_5_2_original_N1024_GO1.kpc
```

**Wait for KnotPlot to complete** before separately running its `_SNAPSHOT.kpc`. There is no automatic GO-then-snapshot shortcut because KnotPlot may execute asynchronously. `GO32` is deliberately separate, and the loader does not change `close`, `max-dr`, collision, or damping parameters. Record `parameters` in KnotPlot and preserve the raw outputs.

## Results and gates

- Source theoretical diagram: 4-plat closure of braid `sigma_2^m sigma_1^-1 sigma_2`.
- m=3,4,5,6: names 5_2, 6_1, 7_2, 8_1; 5/6/7/8 crossings.
- Each knot has a directly calculated Wirtinger/Fox Alexander polynomial and knot determinant; the computed *sampled 2D projection* also has exactly the intended crossings.
- Verified static minimum-separation screens and bit-identical KPT LOCD roundtrips.
- Numerical Borromean pairwise Gauss linking near zero **does not demonstrate Milnor triple linking**.
- KnotPlot runtime `GO`, 3D ambient isotopy after remeshing, finite-core pressure/Euler dynamics and any physical model conclusions have **not** been certified.

`ROUND_FOLDED_TWIST_KNOT_FAMILY_v0.2.0_SPEC.md` describes equations, geometry scope, reproducibility and further qualification gates.

## Provenance

All geometry here is generated deterministically from code in `src/`, rather than relying on legacy KnotPlot relaxations. Do not alter frozen E010/E011/A058/A060 assets; import only in a newly versioned candidate with a raw SHA-256 identity check.
