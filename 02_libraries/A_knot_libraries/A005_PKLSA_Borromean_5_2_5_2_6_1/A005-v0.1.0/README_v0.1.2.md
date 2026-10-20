# PKLSA Borromean 5_2 + 5_2 + 6_1: v0.1.2 runtime diagnostic

**Status: DIAGNOSTIC_ONLY / PHYSICS_UNRESOLVED.** This is a versioned copy of v0.1.1 with *unchanged* source snapshot and v0.1.1 geometries, plus one uniformly scaled copy (2x) and safer, manually separated KnotPlot diagnostic scripts. It is NOT a newly certified seed and does not run finite-core Euler dynamics. Original 5_2 is duplicated as provider: NOT independent.

## Why apparent immobility?

The v0.1.1 5_2 local regions had nonadjacent filament distances of about 0.12656 geometry units: only ~5.5% above KnotPlot's DOCUMENTED default `close=0.12`, if the current installed executable matches the documentation. KnotPlot's default repulsion is close to being active there; it may also be a small display-scale motion. The original v0.1.1 script placed `coords ...after` immediately after `go 1`. KnotPlot documentation warns that `go` may return while relaxation is underway; those immediate snapshots are not reliable as completed steps.

This release creates `SMOKE_SCALE2`: a single GLOBAL scale factor 2 applied to every XYZ coordinate of every component, preserving exact polygonal embedding topology by linear ambient isotopy, but changing the ratio to fixed solver `close`. The v0.1.1 unchanged SMOKE candidate remains the comparison. No solver parameters are changed; scale2 is NOT claimed physically equivalent because the KnotPlot numerical force/repulsion length scales are fixed. No straightening/isolated-knot perturbation may count as a Borromean link confirmation.

## Procedure in KnotPlot (paths relative to extracted package root)

1) Begin original baseline:

```
read diagnostic/01_original_LOAD_BASELINE.kpc
read diagnostic/02_original_GO1.kpc
```

WAIT until KnotPlot finishes the step (red go button no longer active; and check `parameters iteration`). THEN:

```
read diagnostic/03_original_SNAPSHOT_AFTER1.kpc
```

2) Compare actual movement in each region from Windows command prompt:

```
py -3 diagnostic/compare_regions.py diagnostic/original_before.xyz diagnostic/original_after1.xyz
```

3) Repeat with exact SAME steps for globally scale2:

```
read diagnostic/11_scale2_LOAD_BASELINE.kpc
read diagnostic/12_scale2_GO1.kpc
```

WAIT. Then:

```
read diagnostic/13_scale2_SNAPSHOT_AFTER1.kpc
```

Compare:

```
py -3 diagnostic/compare_regions.py diagnostic/scale2_before.xyz diagnostic/scale2_after1.xyz
```

4) If both steps complete, do an additional 32 iterations and manually snapshot:

```
read diagnostic/14_scale2_GO32_MORE.kpc
```

WAIT, then:

```
read diagnostic/15_scale2_SNAPSHOT_AFTER33.kpc
```

Compare from same original baseline:

```
py -3 diagnostic/compare_regions.py diagnostic/scale2_before.xyz diagnostic/scale2_after33.xyz
```

5) Optional isolation test if local knots remain apparently static: load each `40_isolated_*_LOAD_BASELINE.kpc`, execute corresponding `41_*_GO1.kpc`, wait, then `42_*_SNAPSHOT.kpc`. Run `compare_regions.py --region ISOLATED --component-count 1` on the relevant before/after files. These are isolated knotted circles, **not** a Borromean link.

## Acceptance and evidence

- Compare `iteration` before and after. If iteration counter did not increase, 'no motion' is NOT established.
- Compare RMS displacement of `carrier`, `local_knot`, and `bridges` separately. A visibly static knot region can still move substantially in absolute coordinates; compare after removing centroid translation, too.
- All distances and displacements are dimensionless KnotPlot geometry units. `close`, `max-dr`, and `timeincr` should be logged from current executable. Do not silently override them.
- Never use `collision allow` to force movement; topology may change.
- Default `cyl-rad` is a DISPLAY parameter and may make tiny local strands look stuck or merged; changing it changes the rendering only, not the coordinates or dynamics. Visual inspection alone is not qualification.
- `go` runs KnotPlot bead/spring relaxation, not inviscid Euler or PKLSA vortex dynamics.

## Static regression

```
py -3 -m unittest discover -s tests -v
py -3 diagnostic/test_v012.py
```

The 3D local-knot topology and Milnor triple linking remain unverified in an INDEPENDENT topological checker. This remains an engineering diagnostic.

Primary documentation: R. G. Scharein, KnotPlot Manual, https://knotplot.com/manual/commands.html and https://knotplot.com/manual/parameters.html .
