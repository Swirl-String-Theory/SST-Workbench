# A048 v0.1.0 preregistered hypotheses and gates

## H0 — Kelvin/LIA-like null branch

A bending branch obeys, over the preregistered modal window,

\[
\omega_K(k)=\beta k^2.
\]

The fitted power exponent should be near \(p=2\).

## H1 — candidate torsional/material-phase branch

An independent phase branch is modeled as

\[
\omega_\chi^2(k)=c_\chi^2k^2+\Omega_0^2.
\]

In the gapless limit \(\Omega_0\to0\), \(\omega_\chi\propto |k|\), so the power exponent tends to \(p=1\).

## H2 — blind discriminator qualification

The blind analyzer receives anonymous noisy dispersion cases but not their generator labels. After SHA-256 sealing, reveal succeeds only if:

- classification accuracy >= 0.95;
- every case returns finite positive fit parameters;
- median absolute exponent error is <= 0.08 against the corresponding asymptotic generator exponent;
- no blind file contains the canonical SST values checked by `prepare_blind.py`.

This gate qualifies the analysis instrument only.

## H3 — holonomy/gauge consistency

For a closed phase field,

\[
\oint \partial_s\chi\,ds = 2\pi m.
\]

Adding a constant gauge offset to \(\chi\) must leave the discrete winding estimate invariant. The test tolerance is \(10^{-10}\) for the analytic fixture.

## H4 — geometry numerical controls

For a unit circle the numerical curvature must satisfy

\[
\langle\kappa\rangle=1
\]

and torsion must vanish within the test tolerances. The periodic resampler and differential geometry routines must return finite values and a right-handed Bishop frame.

## H5 — PKLSA trefoil ingest

Scientific trefoil ingest is fail-closed. It requires a `(48,1,512,3)` finite `points` array and, when strict mode is enabled, the signed bundle SHA-256

`ffc31331fccaf10a3171e4ccbf3ec0043e56ff681f85cc8b8149932193d736d1`.

## Physical falsification gate (not yet claimable in v0.1.0)

A physical claim requires measured/simulated dynamical frequencies that were **not generated from the torsional candidate equation itself**. The scalar/torsional hypothesis is disfavored if no independent branch remains after resolution, timestep, remeshing, frame/gauge, and finite-core convergence tests, or if all candidate power is explainable by Kelvin/bending modes.
