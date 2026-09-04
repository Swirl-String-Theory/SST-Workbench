# SST Parametric Knot–Link Seed Atlas (PKLSA) v0.1.0

Self-contained **49-family × 48-variant = 2352 candidate** geometry atlas for SST dynamic-seed screening.

## Scope

The 49 family names reproduce the historical `KnotPlot/knots/final` catalog scope. The atlas does **not** copy the relaxed KnotPlot centerlines as its primary geometry. It reconstructs each topology using one of three routes:

1. `knot_3.1`: the 48 PTSA v1.0.0 track-trefoil shapes, preserved up to a global translation/uniform scale normalization.
2. `torus_*`: direct generalized shader-track torus-knot/link parameterization.
3. Other knots/links: Brian Gilbert/Knot Atlas Fourier centerline as the topological base, followed by a single global invertible Shader-Inspired Ambient Family (SIAF) deformation shared by all components. Unknots/unlinks start from analytic circles.

Every family has 48 variants and 512 samples **per component**. Arrays are stored compactly as `families/*.npz`; use `tools/export_candidate.py` to emit the multi-component XYZ format used by the falsifiers.

## Scientific status

`construction_method` is a provenance statement, not a claim of physical stability. SIAF maps are global diffeomorphisms, so they preserve the topology of the base embedding. The atlas independently cross-checks multicomponent families with numerical Gauss-linking integers and the user's historical KnotPlot linking audit. It does not compute a complete knot invariant, so `topology_certified_by_atlas` remains false for single-component knots. Dynamic stability must be tested downstream.

## GPU

GPU is intentionally optional. Atlas generation/validation is CPU-cheap; a full 2352-carrier Biot–Savart dynamics campaign is not. See `gpu_template/`. Recommended workflow: GPU for broad screening, CPU C++/pybind11 for final scientific certification and CPU↔GPU parity.

## Quick use

```bat
python tools\verify_atlas.py
python tools\export_candidate.py PKLSA_<id> candidate.xyz
```

See `VALIDATION.md`, `PROVENANCE.md`, `PARAMETER_GRID.json`, and `manifests/SOURCE_MAP.json`.
