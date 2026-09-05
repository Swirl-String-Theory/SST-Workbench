# v0.3.4 numerical-spectral patch

## Problem closed by this release

The Gilbert source contains Fourier rows through approximately mode 255, while earlier QM/continuum
presets sampled at N=48--512.  N=128 and N=256 are below Nyquist for an unfiltered m=255 source,
and N=512 is only just above strict Nyquist.  Curvature/bending is additionally derivative-sensitive:
small high-mode coefficient rounding is multiplied by m^2 in r''.

## Changes

1. Baseline Fourier geometry uses analytic r' and r''; continuum bending no longer uses second-order
   finite differences.
2. Arbitrary reduced perturbed curves use FFT spectral differentiation rather than second-order
   finite differences.
3. Derivative-sensitive geometry and O(N^2) hydrodynamics now have separate resolution ladders.
4. A cutoff ladder audits m=32,64,96,128,160,192,224,full with analytic derivatives.
5. The ledger reports strict Nyquist and a conservative nonlinear-geometry sampling recommendation.
6. The ledger reports derivative-power tail fractions and a six-decimal source-precision risk flag.
7. QM readiness is blocked when the working geometry is unresolved, or when the combined spectral-tail
   precision-risk gate is unresolved.
8. Explicit filtered QM presets are provided only as RESEARCH TRACK numerical regularizations; the
   cutoff is not promoted to an SST physical parameter.

## Interpretation

`spectral_tail_contaminated_risk=true` means the available coefficient precision and derivative-weighted
high-mode content make bending conclusions unsafe without a cutoff study or higher-precision/Ridgerunner
geometry.  It does not prove those modes are spurious.
