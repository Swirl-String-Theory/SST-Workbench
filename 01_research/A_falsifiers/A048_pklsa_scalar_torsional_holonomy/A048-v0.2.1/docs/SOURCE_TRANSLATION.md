# Source translation: 2014 notebook -> A048

## Source-derived content

The supplied 2014 notebook contains three motifs used to motivate this project:

1. a decomposition of the vector Laplacian into divergence/gradient and curl/curl pieces, with a handwritten contrast between a longitudinal “scalar wave” and a transverse electromagnetic/Hertz wave;
2. a page that explicitly connects a wave-equation sketch to “vortex stretch”, advection, and a moving vortex;
3. later pages that write hyperbolic/parabolic wave-equation forms and damping/conductive terms.

Those notes do **not** contain the modern A048 torsional-phase PDE, a PKLSA construction, a Bishop frame, a Hasimoto map, or a validated independent scalar mode. Those elements are later hypotheses/modeling choices.

## Modern translation used by A048

For incompressible inviscid flow,

\[
\nabla\cdot\mathbf v=0,
\qquad
\partial_t\boldsymbol\omega+(\mathbf v\cdot\nabla)\boldsymbol\omega
=(\boldsymbol\omega\cdot\nabla)\mathbf v.
\]

Therefore A048 does not interpret “longitudinal” as a compressive density wave. The candidate scalar is instead an internal material phase \(\chi(s,t)\) living along a closed vortex tube. Its simplest testable dispersion is

\[
\omega_\chi^2=c_\chi^2k^2+\Omega_0^2,
\]

compared against a Kelvin/LIA-like quadratic null

\[
\omega_K=\beta k^2.
\]

The geometry-only candidate operator

\[
\mathcal L_\chi=-c_\chi^2\partial_s^2+
 a_\kappa\kappa^2(s)+a_\tau\tau^2(s)
\]

is explicitly exploratory. It generates predictions that later independent dynamics must confirm or falsify.
