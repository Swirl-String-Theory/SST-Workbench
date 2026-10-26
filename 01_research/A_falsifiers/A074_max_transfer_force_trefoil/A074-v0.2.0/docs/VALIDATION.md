# Validation v0.2.0 — explicit local evidence

- Status: DEVELOPMENT. Actual v1.0.10 framework run NOT EXECUTED; framework source retained as external dependency.
- Source exact original ideal.txt SHA-256 `a16c0f6e9175fdd54ee8c50b3b32e23caa3b256e7da21145be00a5a58e08cc51`; extracted seed in `seeds/`.
- `pytest -q tests`: **8 passed** (2026-10-26).
- Spectral Euler RHS forms (rotational and convective) agree to floating point in implemented 2/3 Galerkin subspace.
- Nine constrained initial candidates tested. Minimum normal relative equilibrium error = 0.212820133, not less than 0.05.
- Exploratory 330-trial random+coordinate search: discovery best error = 0.229396014, held-out N48=0.207646922; N64=0.213641990.
- PILOT 9 Euler trajectories over fixed T=0.1 s: N32,N48,N64, loads 0,.1,1.6 m/s². Max pressure Poisson residual = 3.25221e-16; max div relative = 5.89995e-17; unforced energy drift <= 2.97999e-09.
- Time half-step at N48, fixed T: relative energy=1.83661e-09, marker length=5.53073e-06.
- Spatial N48→N64 at fixed T: energy mismatch 0.003386 (relative); marker length mismatch 0.001953 (relative).
- Independent perturb modes z2,x3 at N48: max finite-time amplification=0.99907352. N64 perturb NOT EXECUTED.
- Maximum transferable force G8: UNRESOLVED; full Euler run 0.4 s timed out; full provider convergence/native parity NOT RUN; isotopy of gridded vortex-core ridges NOT CERTIFIED.
- Preliminary imposed body acceleration is NOT a knot-localized mechanical force; a first-failure load and stable equilibrium have NOT been measured.
- No private GR reference involved in search. No G9 reveal.
