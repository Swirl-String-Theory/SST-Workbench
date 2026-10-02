# Strict blindness architecture — v0.2.1

## Motivation

The v0.2.0 action path still used canonical SST values to convert the
dimensionless filament calculation into SI energy and frequency before blind scoring.
That is unacceptable for the strongest Universal Action / Planck test because the
absolute dimensional scale may already carry Planck provenance.

v0.2.1 therefore separates three claims.

## UA-A — dimensionless discovery

Pre-reveal:

\[
L=1,\qquad \Gamma=1.
\]

No SST canonical or SI scale is permitted.

Measure

\[
\hat f,\quad \hat\omega,\quad \Delta\hat E,
\]

and test

\[
\hat J_f=\frac{\Delta\hat E}{\hat f},
\qquad
\hat J_\omega=\frac{\Delta\hat E}{\hat\omega}.
\]

## UA-B — classical-continuity null

For a smooth classical mode one generically expects

\[
\Delta\hat E\propto A^2,
\]

hence at approximately amplitude-independent frequency

\[
\hat J_f\propto A^2.
\]

The blind analysis fits

\[
\hat J_f\propto A^{p_A}.
\]

A classical-continuity-like \(p_A\) is a negative control. A universal-action
candidate requires amplitude independence and cross-carrier/resolution convergence.

## UA-C — absolute normalization

Only after blind sealing may an SI scale be supplied:

\[
J_0=\rho\Gamma L^3.
\]

Then

\[
J_f=J_0\hat J_f,\qquad J_\omega=J_0\hat J_\omega.
\]

This stage is eligible for an independent Planck comparison only if the supplied
\(\rho,\Gamma,L\) provenance is itself independent of \(h,\hbar\) and of equivalent
legacy SST closures.

## Enforcement

`sst_wp.blind_guard` statically scans all pre-reveal scientific modules for:
- canonical SST numerical fingerprints;
- imports of reveal/provenance modules;
- canonical SST symbols.

It also scans blind configs and blind CSV column names for SI/action target leakage.

The normal `run_all*.cmd` chains invoke the guard before campaign execution and
again before blind analysis.

## Non-claim

A successful dimensionless universal-action result is scientifically interesting,
but it does not determine an absolute SI quantum by itself.
