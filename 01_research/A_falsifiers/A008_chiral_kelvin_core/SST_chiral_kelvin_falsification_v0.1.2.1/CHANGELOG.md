# Changelog

## v0.1.2.1 — numerical mode-tracking hardening

Pack release of the v0.1.2 numerical hardening layer on top of the
validated v0.1.1 solver (additive `convergence_v012` module).

### Motivation

The v0.1.1 campaign established:

- baseline implementation checks PASS;
- matcher self-overlap approximately unity;
- trefoil scalar-energy convergence reached approximately 0.122 percent
  for N=48 -> 64;
- only 2 of 96 matched trefoil groups passed the v0.1.1 convergence gate;
- several oscillatory branches retained stable frequency and circularity
  while individual eigenvector overlap remained poor.

This suggested near-degenerate eigenspace rotation and/or insufficient core
resolution rather than a simple failure of the hydrodynamic kernel.

### Added

- Core-resolution diagnostic

      eta_a = max(Delta s) / a

  with statuses:

      RESOLVED      eta_a <= 0.5
      DIAGNOSTIC    0.5 < eta_a <= 2
      UNDERRESOLVED eta_a > 2

- Separate strict degeneracy and mode-tracking cluster tolerances.
- Near-degenerate eigenspace clustering.
- Principal-angle cluster overlap.
- Arclength Fourier fingerprints for ring and trefoil modes.
- Left/right eigenvector condition numbers.
- Separate:

      implementation_ok
      numerical_tracking_ready
      physical_interpretation_ready

- Resolution presets:

      quick = 48,64,96
      full  = 64,96,128
      max   = 128,192,256

- Windows CMD runner.

### Interpretation rule

Numerical convergence does not imply a physical trefoil mode.

Physical interpretation requires:

1. numerically trackable eigenspace;
2. resolved core sampling;
3. established relative equilibrium.

The torus trefoil remains frozen geometry in v0.1.2.1.

### Deferred to v0.2.0

- imported ideal-trefoil geometry;
- arclength-controlled resampling;
- Bishop / parallel-transport frame;
- relative-equilibrium solve;
- co-moving linear operator;
- rigid and tangential gauge removal;
- four-state physical mode comparison.


## v0.1.1

- Added N -> N' mode matching.
- Added dimensionless frequencies and growth rates.
- Added circularity diagonalisation in exact degenerate subspaces.
- Added convergence tables and matcher self-test.

Audit outcome:

    implementation_ok = true
    physical_interpretation_ready = false


## v0.1.0

- Finite-core Biot-Savart baseline.
- Analytic Frechet derivative.
- Python/native parity.
- Circulation-reversal gate.
- Mirror-energy degeneracy gate.
- Frozen-geometry spectrum.
- Circularity observable.
