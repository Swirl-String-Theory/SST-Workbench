# Stap 8 — Voeg daarna de trefoil toe

## Doel

Integreer de SST-elektroncenterline

\[
K=3_1=T(2,3)
\]

in het gevalideerde Hopfveld, zonder centerline-knooptype en Hopf-lading te identificeren.

De classificatie is:

\[
\boxed{(K,Q_H)}.
\]

## Gatekoppeling

**H10**, afhankelijk van H0–H9.

## Onafhankelijke invarianten

Centerline:

\[
K=3_1.
\]

Veld:

\[
Q_H\in\mathbb Z.
\]

Er geldt niet automatisch:

\[
K=3_1\Rightarrow Q_H=1.
\]

## Werkpakketten

1. Gebruik een gecertificeerde trefoilcenterline met volledige provenance:
   ```text
   KnotPlot → Ridgerunner → smoothing → SSTcore
   ```
2. Construeer een glad Bishop-/material frame.
3. Registreer:
   \[
   Wr,\qquad Tw,\qquad SL=Wr+Tw.
   \]
4. Bouw \(\Psi_{3_1}\) met de gevalideerde methode uit stap 3.
5. Bereken onafhankelijk:
   \[
   K,\quad Q_H,\quad\mathcal H,\quad Wr,\quad Tw,\quad Lk.
   \]
6. Test gladde vervorming, framingtwist, phase slips, near-contact, reconnection en core-profilevariatie.
7. Maak een eventledger voor veranderingen in \(K,Q_H,\mathcal H,Wr,Tw,Lk\).
8. Zoek voorbeelden waarin \(K\) en \(Q_H\) onafhankelijk variëren.

## H10 passcriterium

Een gecombineerde certificatie vereist:

1. onafhankelijk gecertificeerd centerline-knooptype;
2. integerconvergentie van \(Q_H\);
3. volledige provenance;
4. consistent helicity-/eventledger;
5. geen impliciete gelijkstelling \(K\equiv Q_H\).

## Mogelijke eindstatussen

### Sterke route

\[
(K,Q_H)=(3_1,1)
\]

blijft stabiel en H5–H9 sluiten.

### Gedeeltelijke route

Trefoil en Hopf-lading zijn stabiel, maar spinactie of \(4\pi\)-gate blijft open.

### Verworpen koppeling

De orderparameter levert geen robuust \(Q_H\), of de heliciteitsbridge faalt.

## Output

- trefoilgeometry en provenance;
- \(\Psi_{3_1}\), \(\mathbf n_{3_1}\);
- invariantentabel;
- dynamisch eventledger;
- H10-evidence.

## Niet claimen

- dat de trefoil alleen spin-\(\tfrac12\) veroorzaakt;
- dat ropelength \(Q_H\) bepaalt;
- dat \(Q_H\) elektrische lading is;
- dat H10 open H6–H9 automatisch sluit.
