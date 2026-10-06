# Scientific scope

## Frozen blind admissibility requirements

A candidate photon/eigenmode dispersion closure is admissible only if all of the following are present before comparison with A044/GRB constraints:

1. **Dynamical generator:** time-dependent field equations, a discretized linearized operator, or equivalent evolution law.
2. **Mode identity:** an eigenvector/eigenfunction or mode-family identifier linked to the dynamical generator.
3. **Wave-number axis:** at least three distinct physical or dimensionless wave numbers \(k_i\) with an explicit length normalization.
4. **Frequency extraction:** corresponding \(\omega_i\) measured/eigen-solved from dynamics, not inserted from a target dispersion formula.
5. **Convergence:** at least two resolutions or a residual/error certificate showing numerical stability of \(\omega(k)\).
6. **Independent provenance:** no GRB 221009A transparency, timing, or LIV target scale used to choose the candidate coefficients.
7. **Propagation metadata:** sign/branch and polarization/birefringence behavior documented sufficiently for A044 classification.

Only after these gates pass may

\[
 v_g(k)=\frac{d\omega}{dk}
\]

and

\[
 \delta(E)=1-\frac{v_g(E)}{c}
\]

be exported to A044.

## Non-claims

This package does not assume that a PKLSA knot centerline is a photon, that a geometric Fourier mode is a physical propagating eigenmode, or that arclength harmonics determine physical frequencies. Such identifications require a dynamical closure.
