# Model assumptions -- v0.4.0

1. Incompressible, inviscid, unforced vortex-filament dynamics.
2. Both channels use the same regularized midpoint Biot--Savart discretization as v0.3.
3. Counter-circulation is fixed to `Gamma_plus=+1`, `Gamma_minus=-1` in the reference campaign; absolute circulation is removed by nondimensional time.
4. Tangential filament velocity is treated as a centerline parametrisation gauge and removed during shape-RPO integration.
5. A global proper rotation + translation and one common cyclic vertex shift are quotient symmetries. Independent channel shifts are forbidden.
6. Cross-channel distances at or below the regularization core terminate an orbit search as outside the intended separated-channel regime.
7. A true Floquet interpretation requires an accepted RPO. Frozen local spectra are diagnostics only.
8. The full relative monodromy is currently intentionally restricted to small `N` because finite-differencing the complete nonlinear return map costs `2*(6N)` orbit integrations.
9. The Kelvin readout is preregistered, but no alpha comparison is permitted until H14 passes.
10. The reference seed/time window is finite; failure is not a proof of global RPO nonexistence.
