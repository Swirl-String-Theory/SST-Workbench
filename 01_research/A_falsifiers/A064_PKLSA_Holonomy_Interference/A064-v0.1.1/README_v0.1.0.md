# A064 PKLSA Flow Separatrix Identification & Transport v0.1.0

**PROTOTYPE, not an official v1.0.7 certified falsifier.** A064 is a provisional Workbench index and must be checked in `10_docs/registry/catalog_index.json` before registration. The frozen `SST_Falsifier_Framework_v1.0.7` was read in the connected Google Drive but has **not been embedded, patched, or run** here; this package does **not** forge its gate ledger, signatures, BLIND ZIP or `CANONICAL_FROZEN` status. It can be ported into a genuine generated v1.0.7 instance, using that framework's `tools/new_falsifier.py`.

## Two-stage non-circular method

1. Phase 1 (independent of flux): infer a *candidate* 3D boundary from the **velocity-derived vorticity field**. Sweep fixed enstrophy percentile levels, retain the first closed connected component, seal the chosen surface and discovery data.
2. Phase 2: calculate normal relative motion `(dF/dt + v·grad F)/|grad F|` on the frozen candidate, release tracer pairs on opposite sides, integrate trajectories, re-evaluate the independently detected feature, and test crossing and RK-step refinement. Crucially, simply advecting a mesh is not evidence of an invariant material feature.
3. Phase 3 **NOT YET IMPLEMENTED**: identify and continue 2D stable/unstable invariant manifolds of relevant hyperbolic structures, or rigorous 3D finite-time material transport barriers. Without it, use `material-feature` or `permeable-feature`, **never** `true-separatrix-PASS`.

## Modes (Windows)

```bat
run_all.cmd SELFTEST
run_all.cmd DEMO --grid 31
run_all.cmd SNAPSHOTS --source C:\data\pklsa_3d_velocity.npz --grid 31
run_all.cmd PKLSA_GEOMETRY --source C:\data\5_2_xyz.txt --scale-m-per-unit 1.40897017e-15 --core-m 1.40897017e-15 --gamma-m2-s 9.683619203488876e-9 --duration-s 1e-21 --grid 35
```

`PKLSA_GEOMETRY` uses the frozen **filament** field. It is model-derived simulation, not directly observed Euler flow. The last command illustrates one *explicitly assumed* coordinate calibration, not an experimentally established PKLSA/SST length scale. Avoid using absolute numerical results unless calibration and parameter sensitivity have been audited.

Linux/macOS:

```bash
python -m pip install -r requirements.txt
python -m a064.cli DEMO --grid 31
```

## Required direct velocity snapshot contract

Write an uncompressed or compressed NPZ file with:

- `x,y,z`: increasing 1D axes in meters (each >=5 samples).
- `t`: strictly increasing 1D time stamps in seconds.
- `v`: 5D array `(nt,nx,ny,nz,3)` in meters per second.
- For physical time dependence, use at least **3 time frames** and fine enough temporal spacing to converge `∂t F`; 2 is minimally executable, **not** certifying.

Example writer:

```python
np.savez_compressed('pklsa_3d_velocity.npz',x=x,y=y,z=z,t=t,v=v)
```

`E010-v0.3.1` and `E011-v0.3.0` contain source-qualified **STATIC** centerline geometry and provenance, not this velocity contract. The included raw KnotPlot coordinates `3_1`, `5_2`, and `6_1` are original geometry references from Drive and **are NOT individually shown here to satisfy E011 STATIC_READY**. They are not a substitute for independently approved E011 provider anchors.

## Output structure

```text
A064_PKLSA_Flow_Separatrix_Transport_v0.1.0/
  A064_PKLSA_Flow_Separatrix_Transport_v0.1.0-outputs/
    material/, leaky/, translated/, none/, pklsa_3_1_model/, pklsa_5_2_model/, pklsa_6_1_model/ [DEMO]
      CANDIDATE_DISCOVERY.json  (transport-blind discovery)
      DISCOVERY_SEAL.sha256
      CANDIDATE_SURFACE.npz   (if qualified)
      GATE_RESULTS.json
      GATE_RESULTS.md
  A064-v0.1.0_FALSIFIER_REPORT.pdf
  A064_PKLSA_Flow_Separatrix_Transport_v0.1.0-outputs_PROTOTYPE.zip
```

The ZIP is named `PROTOTYPE`, not `_BLIND`, since v1.0.7 freeze/reveal integrity has not been exercised. `DISCOVERY_SEAL.sha256` seals the canonical discovery JSON, and does not imply a framework-grade blind protocol.

## Limitations / scientific gates

- Enstrophy isosurfaces are **candidate flow features**, not mathematically proven separatrices. A geometry-only closed surface is not sufficient to pass G6. No FTLE/LCS objective extraction or invariant-manifold continuation has yet been implemented.
- For a single frame, the velocity is frozen in time, even for particle paths; physical stationarity is an **assumption**, not observed dynamics.
- On sparse two-time-frame data, finite difference for `∂t|ω|²` can produce false non-material flux. Require time-refinement tests.
- C++ FP64 independent certification, resolution convergence, Euler/pressure-Poisson residuals, hyperbolic manifold continuation, provider-envelope robustness and framework v1.0.7 FREEZE/CERTIFY remain unresolved.
- The branch treats scientifically negative gates as diagnostics worth continuing; provenance and invalid-source states cannot be upgraded to physical PASS.
- Cross-provider qualifying geometry must be read from E011 `STATIC_READY_PROVIDER_ANCHORS.jsonl` / `SEED_CONTRACT_SCHEMA.json` and the actual E010 source paths/hashes. This prototype intentionally has no automatic global `.txt` discovery: arbitrary files must not become 'upstream-independent' evidence.

## Sources

- Frozen v1.0.7 template: https://drive.google.com/drive/folders/1IASDEqmcEQXHyTfppetIGgYnVUsvN5hE
- E010-v0.3.1 source: https://drive.google.com/drive/folders/14sNZ0xYoNkI4a-j2HxPoC51xXb0XwVy7
- E011-v0.3.0 source: https://drive.google.com/drive/folders/1lnHSQxcmQwvlde4WEJo46CGkoJQxXnlH
- A063 Hicks/Hill control: https://drive.google.com/drive/folders/1VahF1utx0oRxPvodYYwsC_jwW8KNgq_W
- A024 threaded-hole separatrix: https://drive.google.com/drive/folders/1UdqRUlegt7zDl6FMtHkJn91XkdLXtRO_

## Additional regression caveat

A true separatrix can occur with zero vorticity in potential flow. The `strain` analytical control has a hyperbolic stagnation point although the closed enstrophy candidate detector rejects it. The software therefore returns `POSSIBLE_HYPERBOLIC_SEPARATRIX_MANIFOLD_UNRESOLVED` and never claims no separatrix globally. The included `data/SYNTHETIC_VELOCITY_SNAPSHOTS.npz` is an API control, not PKLSA data.
