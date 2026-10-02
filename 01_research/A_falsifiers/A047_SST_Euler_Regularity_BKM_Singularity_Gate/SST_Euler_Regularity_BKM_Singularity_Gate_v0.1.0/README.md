# SST Euler Regularity / BKM Singularity Gate v0.1.0 (A043)

A blind, theorem-driven numerical falsification gate for asking whether candidate trefoil vortex seeds display resolution-consistent signatures compatible with finite-time Euler breakdown.

## Scientific status

This package is **not** a numerical proof of Euler regularity or blow-up. It is an upstream adversarial gate. `NO_CONVERGED_BKM_CANDIDATE_IN_WINDOW` means only that the preregistered short-window campaign did not produce a resolution-consistent inverse-vorticity blow-up signature.

## PDE

The solver evolves the 3-D incompressible unforced Euler equations in rotational pseudo-spectral form on a periodic cube:

\[
\partial_t \mathbf u = \mathbb P(\mathbf u\times\boldsymbol\omega),\qquad
\boldsymbol\omega=\nabla\times\mathbf u,\qquad \nabla\cdot\mathbf u=0.
\]

It uses RK4 and 2/3 de-aliasing. A Gaussian tangent-vorticity tube is placed around a T(2,3) trefoil centerline and Fourier-projected to a solenoidal field. An optional localized divergence-free high-frequency packet is aligned with the local principal strain direction.

## Gates

- energy drift `< 5e-3`;
- RMS divergence `< 1e-10`;
- BKM observable `B(t)=integral ||omega||_infty dt`;
- late-window fit of `1/||omega||_infty` versus time;
- blow-up escalation requires `R^2 >= 0.98`, extrapolated `T*` within `1.5 T_end`, at least three numerically valid candidate runs, and `<10%` cross-run `T*` spread.

## Blindness

`BLIND/` exposes hashed case IDs only. Human-readable case labels and SST constants are written only under `REVEALED/` after the blind assessment is frozen. The dimensionless solver does not consume SST constants.

## Run

Windows:

```cmd
run_all.cmd
```

Linux/macOS:

```bash
./run_all.sh
```

Outputs follow the SST convention:

- `./SST_Euler_Regularity_BKM_Singularity_Gate_v0.1.0-outputs/`
- `../SST_Euler_Regularity_BKM_Singularity_Gate_v0.1.0-outputs_BLIND.zip`
- `../SST_Euler_Regularity_BKM_Singularity_Gate_v0.1.0-outputs_REVEALED.zip`
- `../SST_Euler_Regularity_BKM_Singularity_Gate_v0.1.0-outputs.zip`

## Known v0.1.0 limitations

Periodic cube rather than compact support on R^3; moderate grids only; synthetic Gaussian trefoil tube rather than PKLSA/KAtlas/KnotPlot library ingestion; no interval arithmetic; no rigorous a-posteriori PDE certification; inverse-vorticity linear fit is a screening heuristic, not a theorem.
