# A064 v0.3.0 — Kelvin Eigenmodes & Two-Wavepacket Falsifier

**Executed, not blind-certified.** 21 Python regression tests PASS, 20/20 mandatory numerical checks PASS, **0/8 operational propagation/recombination screens PASS**. Scientific G6 remains `UNRESOLVED`; G7's particular packet screen `SCREEN_FAIL`, general physical G7 `UNRESOLVED`.

## Actual operator versus interpretation

The unchanged `src/euler_tangent.py` from v0.2.0 generates a Gaussian-smoothed, divergence-free Fourier-Galerkin initial velocity from the four registered native KnotPlot/PKLSA carriers (see `data/native_registry.json`). `src/kelvin_spectrum.py` defines and applies the **actual** linearized Euler operator in real physical fields, matrix-free:

    L[U]d = P[d × curl(U) + U × curl(d)]

ARPACK returns complex eigenvalues and eigenvectors; eigen residuals, solenoidality, the nonlinear finite-difference Jacobian and nonstationarity are checked. **These are instantaneous frozen-base discrete Euler eigenvectors.** Since U(t) is not proven a relative equilibrium, they cannot yet be interpreted as genuine time-harmonic Kelvin eigenmodes.

`src/wavepackets.py` creates two complex localized, divergence-free filament-directed disturbances with opposite phase-carrier sign. Real and imaginary quadratures are evolved **through the time-dependent 3D Euler tangent operator**, not an ad-hoc 1D Schrödinger or acoustic equation. The independent complex packets are superposed only for detector intensity and cross-term measurements. Tube-weighted energy centroids test whether two expected counter-directed branches actually propagate; neither direction nor collision is forced by the numerical model.

## Results

| Carrier | Max abs detector cross fraction | Verified two-way propagation | Verified collision |
|---|---:|---|---|
| `knot_3.1` | 0.03678 | No | No |
| `knot_5.2` | 0.35414 | No | No |
| `knot_6.1` | 0.15459 | No | No |
| `link_6.3.3` | 0.08779 | No | No |

Trefoil instantaneous leading eigenpairs: N=8: 0.04166 ± 0.26429i; N=12: 0.04565 ± 0.44436i; N=16: 0.04440 ± 0.79014i. **These are not numerically converged branch matches.** No-flow detector drift below 1e-15; numerical RK4 time-step check 5.04e-9; nonlinear finite-difference tangent check 1.07e-12. See `outputs/A064-v0.3.0_results.json` for machine-readable precision, all gates, eigenvectors' residuals and controls.

## Run

On Windows from unpacked version directory:

    run_all.cmd

Linux/macOS:

    bash run_all.sh

Install from `requirements.txt`, verify tests, run `A064_PHASE=PRIMARY` on four source geometries, then `A064_PHASE=CONTROLS` to make all controls and aggregate metrics, generate PDF, package outputs. Separate phases ensure long runs can be resumed *from the beginning of the phase* after infrastructure time-outs. Both phases recompute, do not read cached physics data; the second only reads the recorded in-version primary JSON. Native C++, SYCL and official SST Falsifier Framework v1.0.7 runner are **not exercised** here.

## Source/data boundaries

- Native KnotPlot census v0.1.2 is a single provenance group, geometric parity only; catalogue topology identities unverified, no physical Euler stability qualification.
- Dimensions are numerical KnotPlot/grid units; `core=0.4` is not `r_c`, and eigenvalues are not SI hertz.
- Generic quadratic cross-terms cannot establish an emergent U(1), Z2, or Aharonov–Bohm phase. Global geometry is not a gauge field.
- No genuine closed-loop Kelvin eigenbundle is yet available to parallel-transport, nor two independently demonstrated counterpropagating mode families.
- Only an independently certified, well-resolved *relative equilibrium and mode group velocity* can support the follow-up G6/G7 qualifications.

See `docs/SCIENTIFIC_METHOD.tex` and `outputs/A064-v0.3.0_FALSIFIER_REPORT.pdf`.
