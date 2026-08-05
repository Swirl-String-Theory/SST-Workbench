# 02 — Geometrische \(\alpha\)-kandidaat: van coincidentie naar identificeerbare afleiding

**Status:** `[BRIDGE ANSATZ / SPECULATIVE FIT / OBSTRUCTION RESULT]`

## 1. Kandidaatformule

De huidige finite-cell-kandidaat is:

\[
\alpha^{-1}_{\rm lead}
=
\frac{8\pi}{3}\mathcal L_{3_1}.
\]

Met de gebruikte benchmarkwaarde

\[
\mathcal L_{3_1}=16.371637
\]

volgt:

\[
\alpha^{-1}_{\rm lead}\approx137.15471.
\]

Dit ligt ongeveer \(866\) ppm van de gemeten \(\alpha^{-1}\). Het belangrijke positieve punt is dat \(\alpha\) niet in de evaluatie wordt ingevoerd.

## 2. Wat werkelijk onafhankelijk is

Onafhankelijk:

- de gekozen trefoil-geometrie;
- de numerieke ropelengthbenchmark;
- de algebraïsche evaluatie van \((8\pi/3)\mathcal L_{3_1}\);
- de fout ten opzichte van een pas daarna geraadpleegde externe waarde.

Nog niet onafhankelijk:

- de exacte oorsprong van \(8\pi/3\);
- de keuze van sectorvolume \(4\pi/3\);
- de modecount \(N_p=4\) buiten de huidige ansatz;
- shell weights;
- cell-radius gate;
- hogere-orde termen;
- de ppm-precisie van de ropelengthbron.

## 3. Identificeerbaarheidsprobleem

Een model is niet voorspellend wanneer meerdere vrije correcties één target kunnen repareren. Schrijf algemeen:

\[
\alpha^{-1}_{\rm model}
=
C_{\rm sector}
N_{\rm mode}
W_{\perp}
G_{\rm cell}
\mathcal L_{3_1}
+
\Delta_3+\cdots.
\]

Wanneer vijf sub-percentparameters afzonderlijk de resterende fout kunnen absorberen, identificeert één getal geen van die parameters.

De gatevolgorde moet daarom zijn:

\[
G_0\ (\text{provenance})
\rightarrow
G_1\ (\text{identificeerbaarheid})
\rightarrow
G_2\ (\text{operator/Hessian})
\rightarrow
G_3\ (\text{numerieke closure}).
\]

Een kleine eindfout is irrelevant wanneer \(G_0\) of \(G_1\) faalt.

## 4. Vereiste afleiding van de prefactor

De factor \(8\pi/3\) moet uit één bevroren operator volgen. Een mogelijke structuur is:

\[
\mathcal O_{\rm cell}\psi_{\ell m}
=
\lambda_{\ell}\psi_{\ell m},
\qquad
\lambda_\ell=\ell(\ell+1)-2,
\]

waarbij uitsluitend vooraf gedefinieerde soft/zero/unstable modes worden geteld. Dan moet worden bewezen:

1. waarom precies die operator fysisch is;
2. waarom precies die modes meetellen;
3. waarom het celoppervlak of -volume de gekozen normalisatie heeft;
4. waarom de trefoil-ropelength lineair en niet via een andere functionaal binnenkomt;
5. waarom er geen vrije shell factor resteert.

## 5. Ropelengthprecisie

Een ideal-knot ropelength is doorgaans een numerieke upper bound of critical configuration, geen exact analytisch topologisch invariant. Voor een ppm-claim moet de volledige foutketen worden beheerst:

\[
\sigma_{\alpha^{-1}}^2
=
\left(\frac{8\pi}{3}\sigma_{\mathcal L}\right)^2
+
\left(\mathcal L\sigma_{8\pi/3}\right)^2
+
\sigma_{\rm discretisatie}^2
+
\sigma_{\rm model}^2.
\]

De precision claim mag nooit fijner zijn dan de slechtste van:

- meshfout;
- thickness/reachfout;
- smoothingfout;
- KKT-residu;
- contact-mapconvergentie;
- prefactorprovenance.

## 6. Preregistratieprotocol

Vóór evaluatie:

- kies één trefoilbron;
- leg radius- versus diameterconventie vast;
- leg \(N_{\rm mode}\) vast;
- leg sectorvolume vast;
- sluit alle correctietermen of schrijf ze expliciet met vooraf bepaalde coëfficiënten;
- publiceer de uncertainty budget;
- maak de targetwaarde onzichtbaar voor de optimiser.

Na evaluatie:

- rapporteer de ruwe waarde;
- rapporteer alle onzekerheden;
- pas geen coefficient aan;
- vergelijk éénmaal met CODATA.

## 7. Falsifiers

De kandidaat wordt verworpen als first-principles route wanneer:

1. de prefactor niet uniek uit de operator volgt;
2. de uitkomst sterk verandert onder een gecertificeerde trefoilbron;
3. de radius/diameterconventie niet intern wordt opgelost;
4. een shell weight of cell gate op \(\alpha\) wordt afgestemd;
5. de numerieke onzekerheid groter is dan de geclaimde overeenkomst;
6. andere preregistreerde knopen geen coherente structurereeks geven;
7. een onafhankelijke operator dezelfde prefactor niet reproduceert.

## 8. Verdedigbare huidige conclusie

\[
\boxed{
\frac{8\pi}{3}\mathcal L_{3_1}
\text{ is een }\alpha\text{-vrije sub-per-mille coincidentie,}
\text{ geen unieke afleiding.}
}
\]

De echte researchvraag is niet hoe de resterende \(866\) ppm kan worden weggefit, maar of \(8\pi/3\) en alle correcties vooraf uit één fysische operator kunnen worden bewezen.
