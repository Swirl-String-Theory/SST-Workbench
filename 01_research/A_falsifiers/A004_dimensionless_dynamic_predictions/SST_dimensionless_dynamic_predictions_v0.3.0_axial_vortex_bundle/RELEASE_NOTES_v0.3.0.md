# Release notes v0.3.0

## New research capability

The package now models a finite-radius axial vortex bundle passing through the central aperture of a knot. The bundle can be represented as a continuum Rankine column or as discrete infinite straight vortex tubes.

## Two non-equivalent tube modes

### Physical tubes

\[
\Gamma_{\rm tube}=\text{fixed},
\qquad
\Gamma_{\rm hole}=N\Gamma_{\rm tube}.
\]

Changing \(N\) changes the physical state.

### Numerical discretization

\[
\Gamma_{\rm hole}=\text{fixed},
\qquad
\Gamma_{\rm tube}=\Gamma_{\rm hole}/N.
\]

Changing \(N\) refines the representation and should converge to the continuum bundle.

## Included validation

- 11/11 automated tests pass.
- Fixed-total discrete bundles converge to continuum Rankine.
- At \(N=61\), mean field-RMS error is approximately \(1.76\times10^{-4}\).
- At \(N=61\), mean intrinsic-residual error is approximately \(5.63\times10^{-4}\).
- The tested frozen hole-matched bundles do not stabilize the static ideal trefoil.
- Full 3-D tube backreaction remains open.
