# Validation — 4_SST Maxwell Falsifier v0.2.0

Validation was performed against the supplied `KnotPlot_relaxed_final.zip` snapshot, which contains 41 `*_final.txt` geometries plus their companion metrics/alias sidecars.

## Loader / provenance

- 41/41 final geometries discovered.
- 41/41 loaded without error.
- Multi-component files were split from `vertices_per_component` in the companion `*.metrics.json` files.
- Observed component counts ranged from 1 to 3 and matched the sidecars in the supplied snapshot.

## Synthetic software controls

`pytest` result: **2 passed**.

The seven-test synthetic suite returned:

- T01: PASS
- T02: PASS
- T03: PASS
- T04: PASS
- T05: PASS
- T06: PASS
- T07: REJECTED_NEGATIVE_CONTROL — expected outcome

## Full BASIC campaign

Preset: `N=240` per component.

Native backend validation run:

- backend: C++17 / pybind11
- OpenMP: enabled
- threads: 4
- geometries: 41
- elapsed wall time in this container: approximately **0.70 s**
- T02: 41/41 PASS
- T04: 41/41 PASS
- T05: 41/41 PASS
- T07: 41/41 `REJECTED_NEGATIVE_CONTROL`

The T02 local-meridian radius is capped by the nearest nonlocal/inter-component centreline distance. This was necessary for tightly wound torus links such as `torus_6.21`; a fixed edge-length-only radius can leave the local tubular neighbourhood and is therefore not a valid holonomy probe.

## Full EXTENDED campaign

Resolution ladder: `N=300,600,1200` per component. T05 is evaluated at `N=600`; T02/T04/T07 at all three levels.

Native backend validation run:

- geometries: 41
- resolution rows: 123
- elapsed wall time in this container: approximately **8.93 s** with 4 OpenMP threads
- T02: 123/123 PASS
- T04: 123/123 PASS
- T05: 41/41 PASS at N=600
- T07: 123/123 `REJECTED_NEGATIVE_CONTROL`

The resolution ladder is a numerical quadrature/convergence ladder. Resampling a 300-vertex source to 600 or 1200 points does **not** create new geometric information or upgrade Ridgerunner certification.

## Native build path

The packaged `native_ext.build_ext_if_needed` path was exercised end-to-end in this container: it compiled `cpp/native.cpp`, loaded the extension, reported OpenMP support, and ran the campaigns above. The packaged source intentionally does not include a platform-specific compiled binary; `run_install.cmd` builds the extension for the user's active Windows/Python ABI.

## Scope

These checks validate the implementation and discriminability of the workbench. They do not promote the Maxwell-inspired SST identifications to established physics, and they do not alter the source geometry's certification status.
