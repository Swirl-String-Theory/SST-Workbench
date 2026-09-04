# Changelog

## v0.2.0

- Added provenance-clean Geometry/Fluid → Action Quantum programme.
- Added mass-free QGI specific-action inference:
  \(h/m=\pi g_{\rm eff}^2/(12|c_3|)\).
- Added raw population → phase reconstruction pipeline following the published envelope/Hilbert/cubic/direct-fit structure.
- Added public arXiv PDF Fig. 3 digitization fallback, explicitly marked non-raw.
- Added raw velocity-loop → circulation calculation \(\Gamma=\oint v\cdot d\ell\).
- Added mandatory fluid provenance declaration and forbidden-upstream dependency checks.
- Added uniform-Rankine primary model:
  \(\hbar/M=\Gamma/(4\pi)\), \(h/M=\Gamma/2\).
- Added `G10_SPECIFIC_ACTION_CIRCULATION_CLOSURE` as the primary new gate.
- Added blind dimensionless geometry action coefficients using
  \(a_{\rm proxy}=\min(1/\kappa_{\max},d_{\rm nonlocal}/2)\).
- Explicitly reports leading-order geometry cancellation from \(h/M\).
- Added optional absolute geometry/fluid action branch.
- Added post-2019 SI metrology warning for absolute J·s claims.
- Fixed ambiguous dataset audit counts into discovered/accepted/rejected/skipped.
- Retained shader-derived + relaxed knot sources.
- Retained legacy near-\(h\) relation as `ALGEBRAIC_ECHO_CONTROL`.
- Retained separate BLIND and REVEAL packages.
- Retained setuptools, MSVC `py::ssize_t`, and dual VS2022/VS2026 fixes.
