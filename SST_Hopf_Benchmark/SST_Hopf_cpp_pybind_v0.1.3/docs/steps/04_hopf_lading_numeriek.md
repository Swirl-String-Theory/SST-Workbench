# Stap 4 — Implementeer de Hopf-lading numeriek

## Doel

Bereken \(Q_H\) via drie onafhankelijke routes:

1. spinorconnectie;
2. directorveld plus gauge-reconstructie;
3. preimage-linking.

## Gatekoppeling

**H1, H2 en H3.**

## Route A — Spinor

\[
a_i=-i\Psi^\dagger\partial_i\Psi,
\qquad
f_{ij}=\partial_i a_j-\partial_j a_i,
\]

\[
b_i=\frac12\epsilon_{ijk}f_{jk},
\qquad
Q_H^{(\Psi)}=
\frac{1}{4\pi^2}\int\mathbf a\cdot\mathbf b\,d^3x.
\]

## Route B — Directorveld

\[
f_{ij}
=
\frac12\mathbf n\cdot
(\partial_i\mathbf n\times\partial_j\mathbf n).
\]

In Coulomb-gauge:

\[
\widetilde{\mathbf a}(\mathbf k)=
\frac{i\mathbf k\times\widetilde{\mathbf b}(\mathbf k)}
{|\mathbf k|^2},
\qquad \mathbf k\neq0.
\]

## Route C — Preimage-linking

\[
Lk(C_a,C_b)=
\frac{1}{4\pi}
\oint_{C_a}\oint_{C_b}
\frac{(d\mathbf r_a\times d\mathbf r_b)\cdot
(\mathbf r_a-\mathbf r_b)}
{|\mathbf r_a-\mathbf r_b|^3}.
\]

## Werkpakketten

1. Vergelijk finite differences, spectral derivatives en eventueel discrete forms.
2. Behandel de \(\mathbf k=0\)-mode expliciet.
3. Leg oriëntatie en normalisatie vast.
4. Voer grid- en domeinconvergentie uit.
5. Test meerdere gaugevelden.
6. Gebruik regular values voor preimage-extractie.
7. Rapporteer sluiting en smoothness van de inversebeeldcurves.

## Residuals

\[
\Delta_{\Psi n}=|Q_H^{(\Psi)}-Q_H^{(n)}|,
\]

\[
\Delta_{\rm preimage}=|Q_H^{(n)}-Lk|,
\]

naast \(\Delta_{\rm div},\Delta_{\rm curl},\Delta_{\rm int}\).

## Passcriterium

H1–H3 slagen alleen wanneer alle drie routes binnen één numeriek foutbudget overeenkomen.

## Output

- `hopf_charge_spinor.json`;
- `hopf_charge_director.json`;
- `preimage_linking.json`;
- convergentierapport;
- H1–H3-evidence.

## Niet claimen

- dat bijna-integer op één grid voldoende is;
- dat één gaugekeuze gauge-invariantie bewijst;
- dat \(Q_H\) automatisch dynamisch behouden blijft.
