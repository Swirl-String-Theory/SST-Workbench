
# Gate definitions

## U — Blind Universal Action / Planck Gate

### U1 Frequency consistency
\[
\omega=2\pi f.
\]

### U2 Universal action
Across independent carriers, modes, resolutions and preparations:
\[
J_f=\frac{\Delta E}{f}
\]
must have coefficient of variation below the configured bound.

### U3 Linear spectral scaling
\[
\Delta E\propto f^p,\qquad p=1
\]
within tolerance.

### U4 Reveal-only Planck comparison
Only after U1–U3 are frozen:
\[
J_f\stackrel{?}{=}h,\qquad
J_\omega=\frac{\Delta E}{\omega}\stackrel{?}{=}\hbar.
\]

A match to \(h\) without universality or convergence is a fail.

## A — Wien/Euler similarity
For fixed circulation and scale factor \(a\):
\[
a^2\omega(a)=\mathrm{const}.
\]
Finite-core breakdown must be reported as a function of \(r_c/L\), not hidden by refitting.

## B1 — Energy/inertial mass closure
\[
M_E\simeq M_I.
\]

## B2 — Pressure-monopole universality
Without importing \(G\), test whether
\[
\frac{C_p}{M_I}
\]
is carrier-independent.

## D1 — Knot/fluid statistical closure
\[
\beta_{\rm knot}\simeq\beta_{\rm fluid}.
\]

## D2 — Ideal-flow conservation
\[
|\Delta E_{\rm tot}/E_{\rm tot}|
\]
must remain below the configured numerical tolerance.

## Mandatory anti-circularity rule

The following are forbidden upstream of the reveal stage:
- \(h\) or \(\hbar\) as solver parameters;
- calibrating \(\rho_{\text{core}}\), \(r_c\), \(v\), or amplitudes to the Planck target;
- selecting modes because their action ratio is near the target;
- unit-normalizing the action ratio to one using \(h\) or \(\hbar\).

The blind analyzer rejects target-named columns.
