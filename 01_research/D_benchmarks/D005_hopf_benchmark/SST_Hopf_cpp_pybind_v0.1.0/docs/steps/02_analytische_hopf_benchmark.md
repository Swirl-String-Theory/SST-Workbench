# Stap 2 — Bouw een analytische Hopf-benchmark

## Doel

Valideer de Hopf-rekenketen op een exact bekende configuratie met \(|Q_H|=1\), onafhankelijk van SST en toroflux.

## Gatekoppeling

**H0, H1, H2 en H3.**

## Analytische configuratie

\[
z_1=\frac{2(x+iy)}{1+r^2},
\qquad
z_2=\frac{2z+i(r^2-1)}{1+r^2},
\qquad
r^2=x^2+y^2+z^2.
\]

Dan:

\[
|z_1|^2+|z_2|^2=1.
\]

Neem:

\[
\Psi_H=\begin{pmatrix}z_1\\z_2\end{pmatrix},
\qquad
\mathbf n_H=\Psi_H^\dagger\boldsymbol\sigma\Psi_H.
\]

## Werkpakketten

1. Implementeer \(\Psi_H,\mathbf n_H,a,f,\mathbf b\).
2. Gebruik grids \(N\in\{32,64,128,256\}\).
3. Rapporteer domeingrootte, spacing, stencil en boundary treatment.
4. Bereken \(Q_H\) via de Chern–Simons/Hopf-integraal.
5. Test gladde gauges \(\Psi'_H=e^{i\chi}\Psi_H\).
6. Extraheer inverse beelden van twee reguliere punten.
7. Bereken hun Gauss-linking number.

## Residuals

\[
\Delta_Q(N)=|Q_H(N)-\operatorname{round}Q_H(N)|,
\]

\[
\Delta_{\rm gauge}=|Q_H[e^{i\chi}\Psi]-Q_H[\Psi]|,
\]

\[
\Delta_{\rm link}=|Q_H-Lk|.
\]

## Passcriteria

- **H0:** spinor en director zijn genormaliseerd.
- **H1:** \(Q_H(N)\to\pm1\) met aangetoonde convergentie.
- **H2:** gaugevarianten leveren hetzelfde \(Q_H\).
- **H3:** preimage-linking stemt overeen met de integraal.

## Output

- benchmarkvelden;
- convergentietabel;
- gaugevarianten;
- preimagecurves;
- H0–H3-evidence.

## Niet claimen

- dat de benchmark een SST-deeltje is;
- dat \(Q_H=1\) elektrische lading betekent;
- dat H0–H3 de toroflux-mapping valideren.
