# Stap 5 — Test de heliciteitsbridge

## Doel

Onderzoek of de werkelijke SST-snelheid en -vorticiteit door de Hopf-connectie en -kromming worden gedragen.

De eenvoudige bridge is:

\[
\mathbf u_H=\frac{\Gamma}{2\pi}\mathbf a,
\qquad
\boldsymbol\omega_H=
\nabla\times\mathbf u_H=
\frac{\Gamma}{2\pi}\mathbf b,
\]

\[
\mathcal H_H
=
\int\mathbf u_H\cdot\boldsymbol\omega_H\,d^3x
=
\Gamma^2Q_H.
\]

Deze relatie moet worden getest, niet als definitie van SST-heliciteit worden opgelegd.

## Gatekoppeling

**H5 — Helicity bridge.**

## Algemene decompositie

\[
\mathbf u_{\rm SST}
=
\kappa\mathbf a+\nabla\phi+\mathbf u_\perp.
\]

Het gradiëntdeel draagt geen vorticiteit. Bepaal:

\[
\kappa_*=
\frac{\int\boldsymbol\omega_{\rm SST}\cdot\mathbf b\,d^3x}
{\int|\mathbf b|^2\,d^3x}.
\]

## Lokale residual

\[
\Delta_\omega=
\frac{\|\boldsymbol\omega_{\rm SST}-\kappa_*\mathbf b\|_2}
{\|\boldsymbol\omega_{\rm SST}\|_2+\epsilon}.
\]

## Globale residual

\[
\mathcal H_{\rm SST}
=
\int\mathbf u_{\rm SST}\cdot\boldsymbol\omega_{\rm SST}\,d^3x,
\]

\[
\Delta_{\mathcal H}
=
\frac{|\mathcal H_{\rm SST}-\Gamma^2Q_H|}
{|\mathcal H_{\rm SST}|+\Gamma^2|Q_H|+\epsilon}.
\]

## Werkpakketten

1. Begin met een veld dat bewust uit \(\mathbf a\) is geconstrueerd.
2. Gebruik daarna onafhankelijke SST-solvervelden.
3. Meet \(\Gamma=\oint_C\mathbf u\cdot d\boldsymbol\ell\) onafhankelijk.
4. Vergelijk met de dunne-buisdecompositie:
   \[
   \mathcal H\sim
   \sum_i\Gamma_i^2(Wr_i+Tw_i)
   +
   \sum_{i\ne j}\Gamma_i\Gamma_jLk_{ij}.
   \]
5. Volg \(Q_H,\mathcal H,Wr,Tw,Lk\) tijdens ideale evolutie.
6. Classificeer boundary leakage, phase slips, reconnections en discretisatiefouten.

## H5 passcriterium

Sterke bridge:

\[
\Delta_\omega<\varepsilon_\omega,
\qquad
\Delta_{\mathcal H}<\varepsilon_{\mathcal H},
\qquad
\kappa_*\simeq\frac{\Gamma}{2\pi}.
\]

Zwakke/globale bridge:

\[
\Delta_\omega\not\ll1,
\qquad
\Delta_{\mathcal H}\ll1.
\]

Verworpen eenvoudige bridge:

\[
\Delta_{\mathcal H}\not\ll1
\]

na convergentie- en boundarycontrole.

## Output

- velocity/vorticity snapshots;
- \(\kappa_*\);
- lokale en globale residuals;
- helicity decomposition;
- H5-evidence.

## Niet claimen

- dat één scalar match de lokale velden bewijst;
- dat \(Q_H\) gelijk is aan writhe;
- dat topologische heliciteit de volledige energie bepaalt.
