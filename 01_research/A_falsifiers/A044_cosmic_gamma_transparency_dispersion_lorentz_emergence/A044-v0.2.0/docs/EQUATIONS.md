# Equations used by A044 v0.2.0

All energies in the implementation are converted explicitly to GeV or eV as indicated.

## 1. Published phenomenological dispersion

\[
p^2=E^2\left[1+\left(\frac{E}{E_*}\right)^n\right],\qquad n\in\{1,2\}.
\]

For \(x=(E/E_*)^n\ll1\),

\[
p=E\sqrt{1+x},
\]

so

\[
\frac{v_g}{c}=\frac{dE}{dp}
=\frac{\sqrt{1+x}}{1+(1+n/2)x}
\simeq 1-\frac{n+1}{2}x.
\]

Hence

\[
\delta(E)\equiv1-\frac{v_g}{c}
\simeq\frac{n+1}{2}\left(\frac{E}{E_*}\right)^n.
\]

## 2. Cosmological time delay

For a flat background,

\[
\Delta t_n\simeq\frac{n+1}{2H_0}
\frac{E_h^n-E_l^n}{E_*^n}
\int_0^z\frac{(1+z')^n\,dz'}{\sqrt{\Omega_m(1+z')^3+\Omega_\Lambda}}.
\]

This is used only as a conditional diagnostic because intrinsic source delays are not known a priori.

## 3. Pair-production threshold diagnostic

For a head-on collision between a high-energy photon and a soft background photon, with standard electron dispersion and the subluminal photon dispersion above,

\[
\epsilon_{\rm thr}(E)
\simeq\frac{m_e^2}{E}+\frac{E^{n+1}}{4E_*^n}.
\]

The first term is the Lorentz-invariant limit. The second term shifts the target photon threshold upward, suppressing access to the dense CMB target field at sufficiently high energy.

## 4. Candidate-law extraction

For candidate samples \(\delta_i=1-v_g(E_i)/c>0\), a least-squares fit

\[
\ln\delta = a+n_{\rm eff}\ln E
\]

gives the effective order \(n_{\rm eff}\). For an integer tested order \(n\), each sample implies

\[
E_{*,i}=E_i\left(\frac{n+1}{2\delta_i}\right)^{1/n}.
\]

A true single-scale power law should yield approximately constant \(E_{*,i}\) across the fitted band.
