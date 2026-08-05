# 04 — Route I: boundary-state counting en de entropy-area-hiërarchie

**Status:** `[RESEARCH / OPEN NORMALIZATION PROBLEM]`

## 1. Doel van Route I

Route I probeert de keten te sluiten:

\[
\text{SST microdynamica}
\rightarrow
\text{lokale horizon/KMS-sector}
\rightarrow
S_{\rm rel}
\rightarrow
\eta_A^{\rm SST}\delta A
\rightarrow
\text{focusing}
\rightarrow
\text{effectieve zwaartekracht}.
\]

Wanneer \(c_T=c\) en dezelfde entropyconventie wordt gebruikt, zou gelden:

\[
G_{\rm eff}
=
\frac{c^3}{4\hbar\eta_A^{\rm SST}}.
\]

Het centrale probleem is dus niet alleen de formele thermodynamische brug, maar de absolute microscopische area-density \(\eta_A^{\rm SST}\).

## 2. Huidige positieve resultaten

De eerdere Route-I-pakketten hebben bruikbare structurele onderdelen opgeleverd:

- canonieke veldnormalisatie;
- lokale affine/boost/KMS-structuur onder expliciete aannames;
- relative-entropy/boundary-entropy matching als conditionele brug;
- compacte \(U(1)\)-cellulaire telling;
- expliciete scheiding tussen capacity en relative entropy;
- meerdere no-go-resultaten voor eenvoudige degeneracyroutes.

Deze onderdelen tonen dat de route mathematisch organiseerbaar is.

## 3. Huidige negatieve uitkomst

Een eenvoudige binaire of laag-dimensionale cellulaire telling geeft een area-density die ongeveer \(10^{41}\)--\(10^{42}\) lager ligt dan de gravitational target coefficient.

Symbolisch:

\[
\eta_A^{\rm simple}
\sim
\frac{N_{\rm ch}\ln q}{a_*^2},
\]

terwijl nodig is:

\[
\eta_A^{\rm grav}
=
\frac{c^3}{4G\hbar}.
\]

De verhouding is enorm:

\[
\frac{\eta_A^{\rm grav}}{\eta_A^{\rm simple}}
\gg1.
\]

Dit falsificeert de eenvoudige telling als volledige microstate-uitleg.

## 4. Wat niet mag gebeuren

De hiërarchie mag niet worden gerepareerd door:

- \(L_p\) in het celoppervlak in te voeren;
- \(G\) via \(\alpha_g\), \(t_p\), \(F_{\rm gr}^{\max}\) of een equivalent terug te plaatsen;
- een degeneracyfactor van \(10^{41}\) zonder microscopische carrier te postuleren;
- dezelfde degrees of freedom dubbel te tellen als topology en boundary mode;
- een cutoff op de gewenste uitkomst af te stemmen.

## 5. Mogelijke niet-circulaire routes

### 5.1 Constraint-reduced link-field modes

Tel alleen fysieke boundarymoden na gauge- en Gauss-reductie:

\[
N_{\rm phys}
=
N_{\rm links}
-N_{\rm gauge}
-N_{\rm constraints}
+N_{\rm global}.
\]

De entropy wordt:

\[
S_\Sigma
=
\ln\dim\mathcal H_{\Sigma,\rm phys}.
\]

### 5.2 Entanglement/relative-entropy route

Definieer niet een naïeve bitcount, maar een reduced density operator:

\[
S(\rho_\Sigma)
=-\operatorname{Tr}\rho_\Sigma\ln\rho_\Sigma.
\]

De area law moet uit correlaties en locality volgen, niet uit een vooraf gekozen area coefficient.

### 5.3 Topological order

Onderzoek of een deconfined compact sector een boundary Hilbert space heeft met een extensieve lokale factor plus niet-extensieve topological correction:

\[
S(A)
=
\eta_A A
-
\gamma_{\rm top}
+
\cdots.
\]

Alleen de eerste term kan \(G\) bepalen; \(\gamma_{\rm top}\) is niet groot genoeg om een area-density-hiërarchie te repareren.

### 5.4 Sub-core mode tower

Een tower van fysieke sub-core modes is alleen geldig wanneer:

- de microdynamica hun bestaan afdwingt;
- hun cutoff volgt uit de actie;
- hun energie positief is;
- hun aantal onder refinement convergeert;
- zij niet reeds als coreprofielmode zijn geteld.

### 5.5 Induced-gravity/effective-action route

Integreer microscopische modes uit en zoek een curvatureterm in de effectieve actie:

\[
\Gamma_{\rm eff}
\supset
\frac{1}{16\pi G_{\rm ind}}
\int R\sqrt{-g}\,d^4x.
\]

Dan moet \(G_{\rm ind}\) uit het spectrum en de cutoff van de SST-microdynamica volgen, zonder Planckschaalinput.

## 6. Vereiste berekeningen

1. specificeer één microscopic graph/adjacency law;
2. construeer de fysieke Hilbert space of klassieke phase-space measure;
3. voer gauge reduction uit;
4. bereken boundary rank en spectrum;
5. bepaal locality en correlation length;
6. bereken \(S(A)\) over een resolutieladder;
7. controleer area versus volume law;
8. test regulatoronafhankelijkheid;
9. bepaal of dezelfde microdynamica ook \(c_T\) levert;
10. vergelijk pas daarna met gravitational normalization.

## 7. Gates

### B0 — Geen gravitational input

\[
\frac{\partial\eta_A^{\rm micro}}{\partial G}
=
\frac{\partial\eta_A^{\rm micro}}{\partial L_p}
=0.
\]

### B1 — Fysieke state count

Geen gauge-, constraint- of dubbelgetelde modes.

### B2 — Area law

\[
S(A)=\eta_AA+o(A)
\]

over meerdere geometrieën.

### B3 — Continuumstabiliteit

\(\eta_A\) moet een verklaarde renormalized limit hebben.

### B4 — Positiviteit en causaliteit

Geen ghosts, negative norms of instabiele branches.

### B5 — Cross-sector consistency

Dezelfde parameters moeten zowel boundary count als propagation sector dragen.

## 8. Falsifiers

Route I faalt in de gekozen microbranch wanneer:

1. de entropy volume-law blijft;
2. de area coefficient regulator-divergent is zonder afleidbare renormalisatie;
3. alleen gauge modes de grote telling leveren;
4. de cutoff op \(G\) of \(L_p\) moet worden gezet;
5. de benodigde degeneracy niet in de microdynamica bestaat;
6. dezelfde parameters \(c_T\) en \(\eta_A\) niet tegelijk leveren;
7. de state count dubbel telt;
8. de effective focusing law niet tensorieel sluit.

## 9. Verdedigbare huidige conclusie

\[
\boxed{
\text{De thermodynamische structuur is niet uitgesloten,}
\text{ maar de huidige eenvoudige microstate-telling is onvoldoende.}
}
\]

Het echte target is een onafhankelijk afgeleide fysieke area-density, niet een algebraïsche herschrijving van \(G\).
