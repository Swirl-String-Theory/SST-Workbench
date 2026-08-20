# Method — v0.2.1

## Filament dynamics

Carrier and substrate evolve in one regularized Biot-Savart + local-induction model. Dimensionless time is `tau = |Gamma_core| t`. Global translation, rigid rotation and tangential marker gauge are quotiented before shape residuals are scored.

## Closed substrate

Every substrate thread crosses the carrier passage and closes through a remote return leg. No filament endpoint is introduced. Different bundle members use distinct return sectors.

## Physical contact/CFL mask

A component contributes to physical contact and Kelvin-wave CFL estimates only if

\[
|\Gamma_i|>\epsilon_\Gamma.
\]

Thus null-control ghost threads with `Gamma=0` preserve blind geometry without producing false collisions or time-step restrictions. They remain advected as passive tracers.

## Hierarchical stability score

- full horizon beats a contact-stopped candidate;
- two contact-stopped candidates are compared only by survival time;
- AUC/RPO/modal-growth metrics are used only when both reach the full horizon.

## Dynamic thread focusing

For each recorded geometry the central portions of the thread loops define a geometry-only bundle-radius proxy. The corresponding proxy density is

\[
n_B^{\rm proxy}=\frac{N_B}{\pi R_B^2}.
\]

Active-thread density growth is compared with the identical zero-circulation passive-tracer control.

## Free-space pressure-Poisson

The source

\[
S_p=-\rho\,\partial_i v_j\partial_j v_i
\]

is sampled on a finite Cartesian source grid using non-periodic derivatives. The source mean is not subtracted. Pressure is evaluated at center/shell and radial spherical samples using the open Green function

\[
p(\mathbf x)=-\frac{1}{4\pi}\int \frac{S_p(\mathbf x')}{|\mathbf x-\mathbf x'|}\,d^3x'.
\]

The source moments include

\[
Q=\int S_p\,d^3x,
\qquad
\mathbf D=\int \mathbf x S_p\,d^3x,
\]

plus a quadrupole diagnostic. For the induced active-minus-null field, `Q_delta > 0` is the sign required for a negative `-Q_delta/(4 pi r)` monopole tail.

## Blind far-field fit

Before reveal, the anonymous profile `p_A(r)-p_B(r)` is fit to

\[
A+B r^{-\nu}
\]

with `nu` searched freely. Pair reversal changes only the coefficient sign. Reveal supplies the target comparison only after sealing.

## Convergence

The dedicated far-field campaign varies source-grid resolution and source-box size. Both exponent span and induced-monopole relative span must satisfy preregistered tolerances.

## Pressure coupling law

Symmetric beta scans are decomposed after reveal as

\[
\Delta p=A\beta+B\beta^2+C\beta^3+D\beta^4.
\]

The sign of the even quadratic coefficient is tested carrier-by-carrier.

## Triple gear phase

Marker shifts are not used. For each `T(3,3)` carrier component the phase is derived from its toroidal/poloidal embedded geometry. For each central thread the helix phase is extracted from azimuth versus axial position. Global carrier rigid motion is removed first. Small rational `p:q` relations are discovered, never supplied as targets.

## Confirmation versus discovery

`preset_confirmatory_stability.json` contains four fixed pairs chosen before the new run. `preset_stability_islands.json` is explicitly discovery-only and extends to `|beta|=3`.
