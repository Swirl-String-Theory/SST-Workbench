
# Provenance audit: \(4\pi^2\rho_{\text{core}}v r_c^4\simeq h\)

## Classification

**Result: parameter echo / algebraic closure under the legacy canonical chain.**

The relevant legacy diagnostics contain all three relations

\[
v=\frac{\alpha c}{2},
\qquad
F_{\text{swirl}}^{\max}=\frac{v\hbar}{2r_c^2},
\qquad
\rho_{\text{core}}=\frac{4F_{\text{swirl}}^{\max}}
{\pi\alpha^2c^2r_c^2}.
\]

Substitution gives

\[
\rho_{\text{core}}
=
\frac{2v\hbar}{\pi\alpha^2c^2r_c^4}.
\]

Hence

\[
4\pi^2\rho_{\text{core}}vr_c^4
=
\frac{8\pi v^2\hbar}{\alpha^2c^2}.
\]

Using \(v=\alpha c/2\),

\[
4\pi^2\rho_{\text{core}}vr_c^4
=
2\pi\hbar=h.
\]

No independent physics remains in that equality once the three upstream relations are adopted.

## Numerical residual

With the rounded canonical values shipped in SST:

\[
4\pi^2\rho_{\text{core}}vr_c^4
=
6.6260695156810\times10^{-34}\ {\rm J\,s},
\]

while

\[
h=6.62607015\times10^{-34}\ {\rm J\,s}.
\]

Relative residual:

\[
-9.5731\times10^{-8}.
\]

This is consistent with rounding/precision propagation, not a new prediction.

## What remains scientifically testable

Do not test the algebraic identity again. Test whether free dynamics independently produce

\[
\Delta E/f=h
\]

or equivalently

\[
\Delta E/\omega=\hbar.
\]

The target constants must be absent from the solver, preparation stage, fit, normalization,
and blind analysis. They are permitted only in the final reveal stage.
