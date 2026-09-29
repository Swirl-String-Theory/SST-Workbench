# Provenance-clean Geometry/Fluid → Action Quantum gate

## Dependency graph

Primary branch:

\[
\{\text{QGI population},t,g_{\rm eff}\}
\rightarrow c_3
\rightarrow (h/m)_{\rm QGI}
\]

versus

\[
\{\mathbf x(s),\mathbf v(s)\}
\rightarrow
\Gamma_{\rm fluid}
\rightarrow
(h/M)_{\rm GF}=\Gamma_{\rm fluid}/2.
\]

Forbidden upstream dependencies on the fluid side:

\[
h,\quad\hbar,\quad m_e,\quad r_{\rm Compton/electron},\quad\alpha.
\]

The geometry carrier enters the absolute-action branch as

\[
\widehat L=L/a,
\qquad
h_{\rm GF}
=
\frac{\pi}{2}\widehat L\rho\Gamma a^3.
\]

At leading uniform-Rankine order it cancels from \(h/M\). This cancellation is a derived model
property and is itself part of the falsifier output.

## Why canonical SST \(\Gamma_0\) is excluded from the primary gate

The current canonical chain uses a Compton-locked horn/circulation radius. Consequently
\(\Gamma_0=2\pi r_cv_{\circlearrowleft}\) inherits the calibration provenance of \(r_c\).

It may be shown as a contaminated control after reveal, but it cannot produce a primary
provenance-clean PASS.

## Future v0.3 route

A stronger test should obtain \(\Gamma\), \(a_{\rm core}\), and the velocity-profile shape directly
from a resolved finite-core Euler/vortex-blob simulation whose dimensional boundary data are
independent of quantum constants. Then curvature/twist corrections can be derived rather than fitted.
