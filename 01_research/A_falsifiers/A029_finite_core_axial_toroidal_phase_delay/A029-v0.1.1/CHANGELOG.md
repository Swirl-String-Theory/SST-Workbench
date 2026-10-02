# Changelog

## 0.1.1

- Fix carrier closure statistics to use only pairs where CLOSED and control modes are both converged/valid.
- Fix delay aggregate to use only valid CLOSED modes with successful wave-packet return.
- Neutral/neutral growth is now an explicit tie; numerical near-zero growth cannot create extreme ratios.
- Replace one-sided non-integer closure control by symmetric `k0-dk` / `k0+dk` averaging, cancelling first-order dispersion-slope bias.
- Export Swirl-Clock variables: `Re(lambda)`, `Im(lambda)`, mode period, group velocity, group delay, measured return delay, loop phase, core RMS material swirl, and mode/swirl frequency ratio.
- Add preregistered `m=1` confirmatory phase campaign at `phi*=2.72 rad` on six carriers not used in the v0.1.0 extended discovery set.
- Add matched `m=2` negative-control campaign for branch specificity.
- Add analytic T(3,4) and T(3,5) carriers for independent confirmation.
- Preserve the hard rule that no delay or target phase is supplied to the dynamics.

## 0.1.0

- Initial standalone finite-core axial/toroidal eigenmode blind falsifier.
- Linearized incompressible Euler generalized eigenproblem for three smooth finite-core profiles.
- Closed carrier length + curvature validity + Bishop holonomy.
- Geometric closed-loop wavenumber versus blinded non-integer phase-closure null.
- Eigenbranch continuation, measured group velocity, periodic wave-packet return, and measured loop phase.
- No explicit feedback delay or target phase in dynamics.
- Carrier-cluster statistics and leave-one-carrier-out circular phase/growth permutation gate.
- C++17/OpenMP pybind11 helper and Windows one-click runners.
