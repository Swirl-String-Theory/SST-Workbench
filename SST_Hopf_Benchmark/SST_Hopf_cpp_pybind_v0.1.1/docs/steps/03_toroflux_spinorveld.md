# Stap 3 — Maak een toroflux-spinorveld

## Doel

Map een toroflux-/vortexbuisgeometrie expliciet naar een genormaliseerd veld \(\Psi_{\rm TF}\).

## Gatekoppeling

Primair: **H4**. Voorbereidend op H5.

## Buiscoördinaten

\[
\mathbf x(s,\rho,\varphi)=
\mathbf X(s)+
\rho\cos\varphi\,\mathbf e_1(s)+
\rho\sin\varphi\,\mathbf e_2(s).
\]

Gebruik bij voorkeur een Bishop-/parallel-transportframe om singulariteiten bij \(\kappa=0\) te vermijden.

## Eerste testansatz

\[
\Psi_{m,n}=
\begin{pmatrix}
\cos\frac{\beta(\rho)}2\,e^{im\xi(s)}\\
\sin\frac{\beta(\rho)}2\,e^{in\varphi}
\end{pmatrix},
\]

met

\[
\beta(0)=\pi,\qquad
\beta(\rho\ge\rho_{\rm out})=0.
\]

Test eerst:

\[
(m,n)\in\{(1,1),(1,2),(2,1),(2,2)\}.
\]

De mogelijke relatie \(Q_H\sim mn\) is een hypothese, geen invoer.

## Werkpakketten

1. Kies en documenteer het frame.
2. Definieer longitudinale fase \(\xi(s)\).
3. Leg single-valuedness rond \(\varphi\mapsto\varphi+2\pi\) vast.
4. Kies een glad radiaal profiel.
5. Test seam- en framewissels als gaugeveranderingen.
6. Voer daarna de echte torofluxgeometrie in.
7. Bewaar centerline-, frame- en windingprovenance.

## Tests

- nergens nul;
- single-valuedness;
- framecontinuïteit;
- vaste randwaarde;
- reparametrisatie-invariantie;
- seam-onafhankelijkheid;
- grid- en centerlineresolutieconvergentie.

## H4 passcriterium

Dezelfde torofluxgeometrie moet onder toegestane frame- en seamkeuzes dezelfde topologische sector opleveren.

## Output

- torofluxcenterline en frame;
- \(\Psi_{\rm TF}\), \(\mathbf n_{\rm TF}\);
- windingmetadata;
- H4-evidence.

## Niet claimen

- \(T(2,3)\Rightarrow Q_H=6\);
- dat één mechanische draad de volledige Hopf-fibratie is;
- dat de gekozen ansatz uniek is.
