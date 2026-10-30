# Scientific protocol - candidate A026 history-matched Euler memory test

## Claim and hypotheses

**H0 (observable closure):** for a fixed current knot observable vector `q(t), qdot(t)`, prior data `q(t-d), qdot(t-d)` do not add out-of-sample predictive power at a fixed `t+h`.

**H1 (hidden-state effect):** history does add information, explained by non-observed coupled modes. This is ordinary projected conservative dynamics, *not* a fundamental new memory force. It is compatible with Euler, but not a proof that SST matter or a clock emerges.

The article used two-time conditional measurement to distinguish bath backflow from initial-position differences (Muruga et al. 2026, DOI:10.1038/s41567-026-03442-w). We adapt the **measurement and control structure**, not its isothermal work-bound interpretation.

## Mathematical benchmark

For SI positions `x,y` and frequencies omega_K, omega_B in s^-1:

\[\ddot x+\omega_K^2 x+g y=0,\quad \ddot y+\omega_B^2 y+g x=0,\quad[g]=s^{-2}.\]

The conserved energy is

\[E=\frac{m}{2}\left(\dot x^2+\dot y^2+\omega_K^2x^2+\omega_B^2y^2+2gxy\right).\]

For `omega_K=2/s`, `omega_B=3.1/s`, `g=2/s²`, the stiffness determinant `omega_K² omega_B²-g²=34.44/s^4 >0`; the system is stable and oscillatory, not dissipative.

Eliminating the second oscillator yields

\[\ddot x+\omega_K^2x-\frac{g^2}{\omega_B}\int_0^t \sin[\omega_B(t-s)]x(s)\,ds=-g\,y_{\rm free}(t),\]

where `y_free(t)=y(0)cos(omega_B t)+ydot(0)sin(omega_B t)/omega_B`.

The kernel has units s^-3 and is oscillatory, so no viscosity is inferred. **The synthetic data are NOT an Euler solution.**

## Pilot gate conditions

- G0 PASS: analytic relative Hamiltonian energy error <= 1e-12.
- G1 PASS: uncoupled `g=0` 95% upper bootstrap bound on relative RMSE gain < 0.05.
- G2 PASS: coupled `g=2` 95% lower gain bound > 0.20.
- G2B PASS: history shuffled between independent trajectories does not improve prediction (95% upper gain bound <0.05).
- G3 PASS: history model approaches full hidden-state oracle within 5% RMSE.
- G4–G8: physical Euler, convergence, invariants, phase, independent backend certification UNRESOLVED/NOT EXECUTED.
- G9: NOT APPLICABLE, no target reveal.

The synthetic decisions are only **diagnostic code-validation statuses**, not physical science-pass labels.

## The actual native-Euler extension (not yet implemented)

1. Admit **verified E010** trefoil and independent geometry variants; use the Ruban T(2,3) `B0=77/500` as a separate immutable candidate, not as an automatically stable result.
2. Build a field with physical core width `a`, circulation `Gamma`, pressure and divergence closure. Compare isolated `3_1`, one deformable background filament, multiple fully coupled filaments, discrete vortex lattice, and coarse-grained solid-body rotation.
3. Enforce Kelvin material circulation, energy, momentum/divergence residuals, helicity, core-clearance, topology and remeshing/material-label fidelity.
4. Choose and lock a **measurable scalar or phase carrier** `q(t)` before running: e.g. a Galilean/Euclidean-aligned geometric Fourier mode of the trefoil, plus its time derivative, not generic mesh vertex IDs.
5. Match current observed state and its derivative, circulation, geometry family, numerical grid, physical final time and core model across independent ensembles. Create physically distinct background histories by **evolving the full coupled field**, never by replacing a history label on an unchanged state.
6. Compare full-background oracle, history-augmented and instantaneous models, with train/holdout split by full trajectory and geometrical seed. Use independent history shuffles and distance-matched controls to reject drift and current-state measurement noise.
7. Run separate spatial, temporal (same final physical time), core-width, box-size and perturbation convergence. Finite-core spectral smoothing and filament regularization are different and must not be equated.
8. Use multiple time delays including near-zero and long-lag, and test whether one can resolve a statistically stable memory contribution. Inviscid dynamics **need not** exhibit thermodynamic forgetting.
9. Only after a robust, repeated phase carrier exists consider the clock ratio `d tau/d t_abs = Omega_K/Omega_ref`. A fit to a prescribed SST square-root law is not a derivation.
10. Perform truly independent numerical kernels and parity through the qualified SST Framework v1.1.0 RC2 (or its later validated successor). The current developer prototype is not that instance.

## What would falsify which claim?

- No coupled history signal after adequate physical convergence falsifies the **specific strong history dependence** hypothesis for the tested geometry, background and observable set, not all SST.
- A signal that vanishes when current hidden field is included indicates ordinary **projection memory**, not an additional physical force.
- A signal that remains only at coarse grids or during remeshing is numerical contamination.
- No stable phase / rapidly decorrelating phase makes the proposed **operational clock carrier** invalid in that regime.
- A drifting or nonstationary background prohibits interpreting a spectral peak as an intrinsic clock.
- Even a stable local phase does **not** verify gravitational or relativistic time-dilation laws.

## Analogy

Two coupled springs can exchange energy; observing only one makes its motion appear to depend on its past. The missing spring, not a mysterious new force, carries the hidden state.

## Citations (for LaTeX thebibliography)

```latex
\bibitem{Muruga2026} L. Muruga, F. Ginot, S. A. M. Loos, and C. Bechinger (2026), ``The extraction of work from hidden degrees of freedom,'' Nature Physics, doi:10.1038/s41567-026-03442-w.
\bibitem{Mori1965} H. Mori (1965), ``Transport, collective motion, and Brownian motion,'' Progress of Theoretical Physics 33, 423--455, doi:10.1143/PTP.33.423.
\bibitem{Kelvin1869} W. Thomson (Lord Kelvin) (1869), ``On vortex motion,'' Transactions of the Royal Society of Edinburgh 25, 217--260, https://doi.org/10.1017/S0080456800028175.
```
