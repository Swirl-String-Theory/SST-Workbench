# SST Double-Coil Rolling-Clock v0.2.0

**STATUS: STANDALONE NUMERICAL DEVELOPMENT / NOT A PHYSICAL SWIRL-CLOCK CERTIFICATION.**

## Purpose

Test whether the visibly rolling, closely doubled A006 `3_1_N1024_ORIG` filament exhibits (i) a repeatable *geometric pattern phase* and (ii) a **separate, physically meaningful internal roll phase** after subtraction of best-fit rigid-body rotation. Do **not** interpret a raw phase winding as an independent clock.

This is an independent research prototype, **not** the `05_apps/A003_vortexlab` application and **not** an assigned A-numbered falsifier. Source code is included; it runs without the VortexLab UI.

## Input and provenance

- Geometry: `data/twist_KNOT_3_1_N1024_ORIG.json` extracted in the prior supplied standalone potential-flow prototype from user-provided `A003-v7.6.25b-m1.zip`, originating in the A006 RoundFolded static candidate.
- SHA-256 of this JSON: `17b9f0a767bc64260347f1d3ccfa805f6c2192a76414ce745d558c4e5c1f53d1`.
- SHA-256 of supplied VortexLab package: `fbbc96d4ea3599882d8e685a49017043ae4ef623d1667834a75a61c5c6be0eaf`.
- Numerical semantics transcribed from VortexLab v7.6.25b `velocityCore`: fourth-order Runge–Kutta, local induction with `DELTA.vast=0.25`, `C0=0.1395`, and **bare nonlocal midpoint self-interaction excluding two adjacent source segments**.
- The supplied seed's independent isotopy certification is unresolved; `3_1` is the A006 catalog label, not a claim proven by this experiment.
- No boundary/cylinder, no imposed rotation, no pressure-Poisson solution, no core material frame, no remeshing, no center-lock or background flow, no mutual friction. Fixed numerical core `a_sim/R=0.002`. Coordinates and time are dimensionless (`R_ref=Gamma=1`).
- This is not a native C++/SYCL parity or continuum convergence certification.

## Observables and phase/gauge calculation

Let `(rho,phi,z)` be cylindrical coordinates with respect to the current centroid, `beta=atan2(z,rho-mean(rho))`, and `ds` be the arc-length weights. For a twice-toroidally/three-times-poloidally wound seed,

```
A(t) = integral exp(i*(2*beta-3*phi)) ds / integral ds
phi_raw = unwrap(arg(A(t))) - arg(A(0))
alpha(t) = integral Omega_rigid,z(t) dt
phi_internal = phi_raw + 3*alpha
roll_phase_internal = phi_internal / 2
```

`Omega_rigid,z` comes from a least-squares rigid velocity decomposition after projecting away the unobservable centerline-tangential reparameterization velocity. Under a pure rigid z rotation by `alpha`, `A -> exp(-3 i alpha) A`: the corrected internal phase is **zero**. This is tested numerically.

Important caveat: a material-frame twist and independently marked fluid elements are not present in a centerline model. The least-squares rigid phase is a gauge *diagnostic*, not unique observational proof of core rotation. Nearly circular geometries are ill-conditioned for separating tangential transport and z-axis body rotation.

The raw pattern can complete cycles just because the trefoil-shaped filament undergoes almost rigid rotation. A nonzero *converged* `roll_phase_internal` plus recurrence in an independently defined physical/mathematical observable is required for an independent clock.

## Completed run matrix

| Run | Points | dt | Duration (tau) | Meaning |
| --- | ---: | ---: | ---: | --- |
| `n192` | 192 | 1.5e-5 | 0.0525 | underresolved control |
| `main` | 288 | 1.5e-5 | 0.2625 | 23 apparent cycles; strong numerical contamination |
| `n288_halfdt` | 288 | 7.5e-6 | 0.0525 | time-step control |
| `n384` | 384 | 1.5e-5 | 0.105 | better spatially resolved |
| `n512` | 512 | 1.5e-5 | 0.120 | 10 complete raw pattern cycles |
| `n512_halfdt` | 512 | 7.5e-6 | 0.030 | high-resolution time-step check |

### Principal result

At `N=512`, the **geometric pattern** completes ten measurable cycles with median period about **0.01145498 dimensionless time units**. The raw phase completes 10.4758 turns by `tau=0.12`. The best-fit rigid body rotates through 3.49165 complete revolutions, predicting `-3*3.49165 = -10.47496` turns of the raw winding phase. The remaining internal poloidal phase is only **-0.000419 revolutions**, not ten independent internal oscillations.

The ten observed raw-pattern periods have a coefficient of variation of about **1.11e-5** over this window. The measured geometric winding coherence is `|A|>=0.999566`; the body-frame symmetric nearest-curve root-mean-square Chamfer displacement is below `0.00101 R`. Neither is proof of a true material-phase clock or an exact relative periodic orbit.

### Spatial/time convergence — BODY-SUBTRACTED roll phase at tau=0.0525

| N | Internal poloidal turns | Minimum winding coherence |
|---:|---:|---:|
| 192 | -1.05595 | 0.225 |
| 288 | -0.223315 | 0.916 |
| 384 | -0.009481 | 0.997 |
| 512 | -0.000282 | 0.999 |

At `N=288` with half timestep the corrected phase is `-0.223324` turns; the spatial-discretization error dominates. At `N=512`, halving the timestep changes the corrected phase at `tau=0.030` by less than about `1e-6` revolutions (see CSV). The high-resolution results show **no converged, nonzero additional internal oscillator**.

### Conclusion

**CONFIRMED in this model:** a coherent, repeated torus-knot *geometric pattern* is induced by its own vortex dynamics; it behaves approximately as a rigidly rotating/propagating state over the tested interval and needs no external rotation.

**NOT CONFIRMED:** an extra internally rolling clock mode distinct from that rigid pattern. As spatial resolution improves, the initial purported internal clock phase disappears.

**NOT ASSESSED:** very long-time stability, point-to-segment/segment-to-segment first-contact certification, global knot isotopy, material core twisting, full incompressible finite-core Euler evolution, external potential flow effects, physical SST time dilation.

## Files

- `rolling_clock.py`: full source sampler, numerical velocity/RK4, geometric winding phase, normal-projected rigid fit, unit invariances; can run a complete parameterized trajectory (long run).
- `chunk_runner.py`: resumable deterministic fixed-step integration. A fresh `chunk 0` followed by successive chunks is identical to one continuous RK4 run with the same settings.
- `analyze_runs.py`: collects chunks, computes phase/period/coherence/shape recurrence and generates plots.
- `test_gates.py`: five numerical parity/invariance/geometry tests.
- `results/*_chunk*.npz`: archived deterministic snapshots and raw measurements; contains full centerline arrays, timestamps and metrics.
- `results/*_processed.csv`: time, rigid motion, raw phase, corrected phase and geometry metrics.
- `results/*_shape.csv`: frame-aligned symmetric nearest-curve distance to initial geometry.
- `results/overall_summary.json`: structured verdict and run matrix.
- `results/internal_phase_resolution.png`, `raw_vs_rigid_phase.png`, `coherence_n512.png`: plots.

## Run

```
python -m pip install -r requirements.txt
python test_gates.py
# or use run_all.sh / run_all.cmd for the full matrix
python chunk_runner.py --chunk 0 --steps 2000 --N 512 --prefix n512
python chunk_runner.py --chunk 1 --steps 2000 --N 512 --prefix n512
python chunk_runner.py --chunk 2 --steps 2000 --N 512 --prefix n512
python chunk_runner.py --chunk 3 --steps 2000 --N 512 --prefix n512
python analyze_runs.py
```

`analyze_runs.py` requires all named runs in the run matrix and is already executed in this package. To produce fresh results from zero use `run_all.sh` or `run_all.cmd`.

## Next physics gates

1. Repeat at `N=768/1024` with an **independent finite-core formulation**, spatial and temporal convergence, and an exact nonlocal segment contact witness; retain failures.
2. Establish spectral/Floquet stability of the rotating shape in a fully specified symmetry-reduced frame, *not* a raw geometric phase count.
3. Introduce a physically material and objective core twist marker (fluid tracer plus frame or resolved vorticity tube) to measure actual internal rotation.
4. Compare a true toroidal unknot `T(2,1)` with a verified trefoil `T(2,3)` and a simple ring `0_1`, matching thickness/circulation and normalized geometry; classify any topological signatures.
5. Only after an independently certified clock, test uniform and nonuniform potential flow, and compare to any SST clock postulate.

## Literature

- Maggioni, F., Alamri, S., Barenghi, C. F., Ricca, R. L. (2010), *Velocity, energy, and helicity of vortex knots and unknots*, Physical Review E **82**, 026309, https://doi.org/10.1103/PhysRevE.82.026309.
- Saffman, P. G. (1992), *Vortex Dynamics*, Cambridge University Press, https://doi.org/10.1017/CBO9780511624063.
