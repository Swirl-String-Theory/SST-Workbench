# Scientific scope and preregistration notes

## Primary observable

\[
\Delta\phi=-\frac{m g^2T^3}{3\hbar}.
\]

The phase is compared against a separately integrated classical action and against the
accelerated-frame gauge boundary term. The code must not derive the action closure by
calling the target phase function.

## Preregistered gates

| Gate | Quantity | BASIC threshold | EXTENDED threshold |
|---|---|---:|---:|
| G1 | cubic exponent \(|p-3|\) | \(5\times10^{-3}\) | \(5\times10^{-4}\) |
| G2 | SST-vs-QGI prefactor relative error | \(5\times10^{-2}\) | \(2.5\times10^{-2}\) |
| G3 | numeric lab-action relative error | \(2\times10^{-5}\) | \(2\times10^{-6}\) |
| G4 | lab/gauge-frame action closure | \(2\times10^{-12}\) | \(2\times10^{-13}\) |
| G5 | \(a=g\) generalized-law identity | \(2\times10^{-14}\) | \(2\times10^{-14}\) |
| G6 | finite-pulse \(T_{\rm kick},T_d\to0\) limit | \(2\times10^{-14}\) | \(2\times10^{-14}\) |
| G7 | blind integrity | exact | exact |
| G8 | source-family coverage after reveal | shader + relaxed | shader + relaxed |

G2 is an **experimental-compatibility gate**, not a proof that the SST action-scale
formula is correct.

## Knot policy

No geometry-dependent correction factor is inserted into the QGI phase in v0.1.0.
Doing so without a canonical SST derivation would amount to adding an unregistered free
model. Geometry is therefore restricted to:

- provenance robustness,
- discretization diagnostics,
- future coupling readiness.

## Falsifying outcomes

The package reports a falsifier hit if any of the following occurs:

- numerical action does not converge to the QGI action;
- frame/gauge closure fails;
- \(T^3\) scaling fails;
- generalized acceleration identity fails;
- finite-pulse limit fails;
- blind manifest / commitment integrity fails;
- a claimed source-complete run is missing either relaxed or shader-derived carriers.

## Interpretation

A full v0.1.0 PASS establishes only that the preregistered macro action/gauge closure and
the SST action scale are compatible with this QGI precision. It does not establish the
microscopic SST mechanism.
