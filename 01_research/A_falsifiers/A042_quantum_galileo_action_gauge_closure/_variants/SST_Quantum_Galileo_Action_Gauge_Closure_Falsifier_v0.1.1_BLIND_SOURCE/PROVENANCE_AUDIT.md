# Provenance audit — why the old near-\(h\) relation is not a blind discovery

v0.1.0 computed

\[
h_{\rm legacy}
=
4\pi^2\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4.
\]

Numerically this lies extremely close to Planck's constant. However, under the legacy SST
definition chain,

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}=\frac{\alpha c}{2},
\]

\[
F_{\rm swirl}^{\max}
=
\frac{\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\hbar}{2r_c^2},
\]

and

\[
\rho_{\text{core}}
=
\frac{4F_{\rm swirl}^{\max}}
{\pi\alpha^2c^2r_c^2}.
\]

Substitution gives

\[
\rho_{\text{core}}
=
\frac{2\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\hbar}
{\pi\alpha^2c^2r_c^4},
\]

hence

\[
4\pi^2\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4
=
\frac{8\pi\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}^2}
{\alpha^2c^2}\hbar.
\]

Using

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}
=
\frac{\alpha c}{2}
\]

then gives exactly

\[
4\pi^2\rho_{\text{core}}
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}r_c^4
=
2\pi\hbar
=
h.
\]

Therefore this is an **algebraic parameter echo** under the legacy provenance chain, not
an independent prediction of Planck's constant.

## Consequence

A target-blind program may still output \(h\) if \(h\) entered upstream through its inputs.
Therefore "the code never read \(h\)" is necessary but not sufficient for a genuine blind
Planck prediction.

A genuinely independent SST Planck gate requires an action observable

\[
J_{\rm SST}[\mathcal K,\text{fluid observables}]
\]

constructed from inputs whose provenance contains no \(h\) or \(\hbar\), sealed before the
Planck target is revealed.
