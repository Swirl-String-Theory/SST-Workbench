# A054 Blind Topological Particle Spectrum Falsifier v0.1.0

## Purpose

Blindly screen **all 35 non-trivial prime knots with 3–8 crossings** and **all 47 prime links with ≤8 crossings** before opening any Standard-Model or historical SST/VAM labels.

The historical quark hypothesis is reveal-only:

\[
u \leftrightarrow 5_2,\qquad d \leftrightarrow 6_1.
\]

The earlier `6_2/7_4` note is explicitly treated as erroneous and is not part of the blind stage.

## What is self-contained

`data/atlas_pd.json` contains all 82 Planar Diagram (PD) presentations. No KnotPlot, PKLSA, SnapPy, KnotInfo, network download or Google Drive access is needed to run v0.1.0.

The PD data were extracted from the Knot Atlas `KnotTheory`` database:
- `PD4Knots.m` blob `479cede40bab464e22e4516b914a45302f907cce`
- `PD4Links.m` blob `8f54a79591725ddf578877b65021822f48966a02`

## Scientific scope

v0.1.0 is a **screening falsifier**, not yet the production vortex-dynamics campaign.

Each PD presentation is converted into several deterministic 3D realizations with randomized presentation lanes. The Python/C++ kernels then measure:

- total polyline length after common normalization;
- discrete bending energy;
- non-local contact distance and contact ratio;
- regularized Neumann/Biot–Savart-like line-integral proxy;
- regularized Gauss self-writhe proxy;
- inter-component Gauss linking matrix;
- embedding-to-embedding coefficient of variation.

These are used to test whether structures form robust blind neighborhoods and whether reveal-only mass-ratio patterns are unusually easy to reproduce.

They are **not** PKLSA-relaxed energies, Euler equilibria, Kelvin eigenfrequencies, Floquet multipliers, or physical particle masses.

## Run

From this directory on Windows:

```bat
run_all.cmd
```

Default `basic` performs all 82 cases with 2 embedding replicates.

For the heavier campaign:

```bat
run_all.cmd full
```

To stop before opening the reveal:

```bat
run_blind_only.cmd full
```

A Python-only diagnostic path exists, but the normal template is strict C++17/pybind11/OpenMP:

```bat
run_python.cmd basic
```

## Pipeline

1. create/update `.venv`;
2. install build requirements;
3. compile `a054_native` with C++17 + OpenMP;
4. enforce Python↔C++ numerical parity;
5. generate fresh HMAC opaque case IDs;
6. freeze configuration and provenance hashes;
7. run all 82 cases without SM or historical labels;
8. write `FEATURES.*`, all pair distances, gates and `REPORT_BLIND.md`;
9. recursively SHA-256 seal the BLIND tree;
10. verify the seal before reveal;
11. open the corrected historical `5_2/6_1` hypothesis and fixed PDG-2026 mass snapshot;
12. run scale-free three-state mass-pattern searches with a random-target look-elsewhere diagnostic;
13. emit BLIND, REVEALED and combined ZIP archives.

## Interpretation gates

A low mass-ratio error is **not** a particle discovery. Promotion to v0.2.0 requires PKLSA/finite-core geometry and dynamical observables under the same blind protocol. Higgs identification specifically remains `NOT_TESTED` in v0.1.0 because scalar-mode character, spin, couplings and electroweak structure are absent.

## Expected output names

- `A054_Blind_Topological_Particle_Spectrum_Falsifier_v0.1.0-outputs/`
- `...-outputs_BLIND.zip`
- `...-outputs_REVEALED.zip`
- `...-outputs.zip`

