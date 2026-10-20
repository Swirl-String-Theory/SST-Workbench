# A065 v0.3.5 — Direct high-resolution historical trefoil qualification

Preregistration SHA256: `2e36f33e328020fd0942d89573fda8a774f6e41e1e2a8245ef46edf33f23113a`

This release supplements and does not retroactively alter v0.3.4's original source manifest,
legacy original D01/D02/D03 seals, G2/G11, or failed coarse G13. No physical promotion.

## Scientific test
For each historical trefoil A and B (original dimensionless coordinates), use direct
analytic-curve equal-arclength sampling at N=600,1200,2400,4800, with identical
Gamma=1 and final time T=0.04, fixed epsilon per run, 8-step RK4.
There is **no rescaling between A and B** and **no upstream data provider** added.

At identical coarse indices, define

E(N,2N) = RMS(X_N(T) - X_{2N}(T)[::2]) / RMS(X_N(T)-X_N(0)).

We preregister BASELINE epsilon=.12, requiring all three errors <1% for BOTH
seeds (G16); values below .1% are reported as a more stringent **diagnostic target**,
not a post-hoc revision to G16. Additional eps=.06/.24 are independent fixed-core
sensitivity scans, with pass/fail reported for all pairs, not force calibration.

G18 performs Python/C++ RK4 full trajectory parity at N150 for both seeds, and
separate 4/8/16 time comparisons at N1200 and N4800, fixed epsilon .12 and T .04.
Python parity at 150 DOES NOT certify Python throughput at N4800 or the Euler PDE.

G15 integrity; G16 baseline spatial convergence; G17 full core scan data
completion; G18 native/parity/temporal controls. All require G1 and G15 only,
not original G2 or G13. G3 remains gated by G1/G10 (v0.3.3), not these new
historical tests.

Input XYZ old 600/1200 files are unchanged; N2400/N4800 were evaluated
**directly** from original analytic parametrizations by `regenerate.arc_sample`
with high-density quadrature (not interpolated from N1200 point coordinates).
All six mesh resolutions from historical G13 and current G16 are recorded,
and the older FAIL is retained.

**Interpretation:** a regularized dimensionless vortex-filament ODE benchmark;
NOT a full incompressible Euler/pressure-Poisson solution, PKLSA dynamics,
Casimir response, gravity, laboratory force or experimentally derived core scale.

## Reproduction
`run_all.cmd VERIFY` then `run_all.cmd SELFTEST`, then `run_all.cmd HIGHRES`,
then optionally `run_all.cmd ALL` using external frozen v1.0.7.
Set `A065_THREADS=4` or 8/16 for optional native CPU OpenMP.
No GPU backend is certified; G6/G7 remain NOT APPLICABLE.
