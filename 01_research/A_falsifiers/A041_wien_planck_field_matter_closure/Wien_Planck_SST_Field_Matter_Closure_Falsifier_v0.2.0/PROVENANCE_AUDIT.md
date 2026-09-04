# Provenance audit v0.2.0

The numerical coincidence
\[
4\pi^2\rho_{\rm core}\mathbf v_{\!\boldsymbol{\circlearrowleft}}r_c^4\simeq h
\]
is classified as a **parameter echo if the legacy defining chain is retained**.

Algebra:
\[
\rho_{\rm core}=\frac{4}{\pi\alpha^2c^2r_c^2}\frac{v\hbar}{2r_c^2}
=\frac{2v\hbar}{\pi\alpha^2c^2r_c^4},
\]
so
\[
4\pi^2\rho_{\rm core}vr_c^4
=\frac{8\pi v^2\hbar}{\alpha^2c^2}=2\pi\hbar=h
\]
when \(v=\alpha c/2\).

v0.2.0 therefore forbids `rho_core`, `F_swirl_max`, `h`, and `hbar` in pre-reveal action extraction/scoring. The dynamical test uses the independent effective fluid density \(\rho_{\!f}\) for its line-energy diagnostic.
