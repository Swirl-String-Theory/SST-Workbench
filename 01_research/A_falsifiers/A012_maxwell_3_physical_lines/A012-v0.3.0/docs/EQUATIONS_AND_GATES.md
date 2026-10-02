# Equations and gates — v0.3.0

## M6 — circulation/linking

For disjoint closed curves `K` and `C`,

\[
\operatorname{Lk}(K,C)=\frac{1}{4\pi}\oint_K\oint_C
\frac{(d\mathbf r_K\times d\mathbf r_C)\cdot(\mathbf r_K-\mathbf r_C)}{\lVert\mathbf r_K-\mathbf r_C\rVert^3}.
\]

For a thin vortex filament of circulation `Gamma`,

\[
\mathbf u(\mathbf x)=\frac{\Gamma}{4\pi}\oint_K
\frac{d\mathbf r'\times(\mathbf x-\mathbf r')}{\lVert\mathbf x-\mathbf r'\rVert^3},
\]

and therefore

\[
\oint_C \mathbf u\cdot d\boldsymbol\ell=\Gamma\,\operatorname{Lk}(K,C).
\]

Blind numerical units set `Gamma=1`. The fit is

\[
Q=a+b\operatorname{Lk},
\]

with preregistered targets `a -> 0`, `b -> 1`, `R^2 -> 1`.

Dimensional check after SI scale restoration:

\[
[Q]=[\Gamma]=\mathrm{m^2\,s^{-1}}.
\]

## M7 — mutual helicity

For disjoint thin tubes,

\[
H_{\rm mutual}=2\sum_{i<j}\Gamma_i\Gamma_j\operatorname{Lk}_{ij}.
\]

Blind runs use `Gamma_i=1`. Maxwell-3 computes the left-hand side from cross-component Biot--Savart line integrals and E010 supplies exact polygonal `Lk_ij` on the right-hand side.

For one centerline, self-helicity is not gated because `Tw` requires a framing/core-director field not supplied by a centerline alone.

## M1--M3 — stress anchor

The coarse-grained momentum-flux tensor is sampled around the admitted PKLSA centerline. The anisotropy coefficient remains

\[
C_{\rm blind}=\frac{p_\perp-p_\parallel}{\rho_{\!f}\,\lVert\mathbf v_{\!\boldsymbol{\circlearrowleft}}\rVert^2}.
\]

Historical coefficients are absent from blind decision code and are comparison-only after reveal.
