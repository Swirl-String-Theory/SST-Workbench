# VortexLab — hoge-resolutie analyse en ontwikkelroadmap

**Project:** SST / VortexLab  
**Bronversie:** VortexLab v7.6.21–v7.6.22  
**Status:** Research Track · niet-canoniek · geen afgeleide klokwet  
**Datum:** 15 juli 2026

---

## 1. Executive summary

De feitelijke benchmarkanalyse is grotendeels sterk. De speculatieve fysicaherinterpretatie bevat bruikbare onderzoeksrichtingen, maar maakt op enkele cruciale punten een te grote sprong van numerieke decompositie naar fysica.

De huidige resultaten ondersteunen de volgende strikte conclusie:

\[
\boxed{\text{De veldroute is een kinematische Swirl-Clockdiagnose.}}
\]

\[
\boxed{\Omega_{\rm body}\text{ is een globale geometrische rigid-bodyrespons, geen interne klok.}}
\]

\[
\boxed{\text{De huidige ROT}\times\text{MUTUAL-term is nog geen bewijs van frame-dragging.}}
\]

\[
\boxed{\text{Een echte interne fase kan niet uit het huidige centerline-model worden afgelezen.}}
\]

De juiste onderzoeksvolgorde is daarom:

\[
\boxed{
\text{convergentie}
\rightarrow
\text{gerichte veldroute}
\rightarrow
\text{afstand/oriëntatie}
\rightarrow
\text{material frame}
\rightarrow
\text{velocity-gradienttensor}
\rightarrow
\text{interne fase}
\rightarrow
\text{holdoutvalidatie}
}
\]

De meest relevante positieve aanwijzing is niet de numerieke nabijheid van een specifieke \(\kappa_{\rm geom}\), maar dat de mutuale interactie tegelijk:

1. een reproduceerbare globale rigid-bodyrotatierespons veroorzaakt;
2. een stabiele A/B-tekenpariteit toont;
3. een kinematische veldcorrectie van orde \(10^{-22}\) produceert;
4. een vrijwel proportioneel tijdstraject oplevert;
5. robuust kan worden gescheiden van de numerieke regularisatieschaal \(a_{\rm sim}\).

Dat rechtvaardigt een strengere interne-fasebenchmark, maar nog geen claim van fysische tijdsdilatatie.

---

## 2. Feitelijke beoordeling van de v7.6.21-benchmark

### 2.1 Technische meetlaag

De technische meetlaag functioneert betrouwbaar:

- alle ENGINE-gates slagen;
- snapshots blijven puur;
- de velocity-decompositie reconstrueert het invoerveld tot machineprecisie;
- de Shapley-decompositie sluit;
- de normalisatie- en transfer-lawroutes zijn deterministisch;
- de lengte-identiteiten sluiten numeriek exact;
- de actuele SST-notatie \(v_{\!\circlearrowleft}^{\ast}\) wordt consequent gebruikt;
- de gekalibreerde route is correct gedefinieerd als actuele waarde minus kalibratiewaarde.

Daarmee geldt:

\[
\boxed{\text{De huidige FAIL- en WARN-resultaten zijn geen programmeerfouten.}}
\]

Ze hebben betrekking op interpretatie, resolutie en ontbrekende fysische afleiding.

### 2.2 Lengte-identificatie

De fysisch bedoelde lengte is:

\[
L_K=\operatorname{Len}(\gamma_K)=\oint_K ds.
\]

Voor de huidige trefoilrun geldt ongeveer:

\[
L_K \approx 0.718525\ {\rm m}.
\]

De onafhankelijke ideal-tube-reconstructie:

\[
L_K^{\rm ideal}
=
\operatorname{Rop}_{\rm diam}(K)\,2a_{\rm core}^{\rm reach}
\]

komt hiermee overeen tot subprocentniveau.

Voor de Gilbert ideal trefoil geldt:

\[
\operatorname{Rop}_{\rm diam}(3_1)=16.371637.
\]

Daarom:

\[
L_{3_1}=16.371637\cdot 2a_{\rm core}.
\]

De datafile gebruikt \(D\) als diameter. De radiusconventie is daardoor:

\[
\operatorname{Rop}_{\rm rad}
=
2\operatorname{Rop}_{\rm diam}
=
32.743274.
\]

### 2.3 Negatieve controle met \(a_{\rm sim}\)

De kandidaat:

\[
L_{\rm sim}=16.371637\cdot2a_{\rm sim}
\]

komt numeriek dicht bij de formele veldschaal wanneer \(a_{\rm sim}=1\ {\rm mm}\), maar de \(a_{\rm sim}\)-sweep toont dat de uitkomst lineair met deze vrije numerieke regularisatie meeschuift.

Daarom geldt:

\[
\boxed{L_{\rm sim}\text{ is geen fysische identificatie van }L_K.}
\]

De echte centerline-lengte verandert over dezelfde \(a_{\rm sim}\)-sweep slechts op promilleniveau en is daarmee de robuuste geometrische kandidaat.

---

## 3. De identiteit \(v_{\!\circlearrowleft}^{\ast}u/c^2\)

De bestaande veldbracket is numeriek ongeveer:

\[
|\delta\ln R_{\rm field}|\approx2.22\times10^{-22}.
\]

Tegelijk geldt:

\[
\frac{v_{\!\circlearrowleft}^{\ast}u}{c^2}
\approx2.22\times10^{-22}.
\]

Deze overeenkomst volgt direct uit de gebruikte kinematische Swirl-Clockformule:

\[
\eta(v)=\sqrt{1-\frac{v^2}{c^2}},
\]

waarbij de simulator de envelope evalueert bij:

\[
v=v_{\!\circlearrowleft}^{\ast}\pm u_{\rm RMS}.
\]

Voor:

\[
u\ll v_{\!\circlearrowleft}^{\ast}\ll c
\]

volgt:

\[
\delta\ln\eta_\pm
\approx
\mp
\frac{v_{\!\circlearrowleft}^{\ast}u}{c^2(1-\beta_0^2)},
\qquad
\beta_0=\frac{v_{\!\circlearrowleft}^{\ast}}{c}.
\]

Omdat:

\[
1-\beta_0^2\approx0.9999867,
\]

is dit praktisch gelijk aan:

\[
\frac{v_{\!\circlearrowleft}^{\ast}u}{c^2}.
\]

### Interpretatie

De overeenkomst is fysisch consistent, maar niet onafhankelijk ontdekt: zij is grotendeels ingebouwd in de definitie van de huidige veldbracket.

Bovendien gebruikt de huidige route een RMS-grootheid:

\[
u_{\rm RMS}
=
\sqrt{
\frac{\oint(\mathbf u_{\rm mutual}\cdot\hat{\mathbf t})^2ds}{\oint ds}
}.
\]

Door het kwadraat verdwijnt het lokale teken. Daardoor kan de bestaande envelope zelf geen gerichte chiraliteit of co-/contra-rotatie voorspellen.

De volgende stap moet daarom een **signed, punt-voor-puntveldroute** zijn.

---

## 4. Correctie op de gerapporteerde schaalfactor

De globale body-proxy is ongeveer:

\[
|\Delta\ln R_{\rm body}|\sim1.6\times10^{-9}.
\]

De veldroute is ongeveer:

\[
|\Delta\ln R_{\rm field}|\sim2.22\times10^{-22}.
\]

De verhouding is:

\[
\frac{1.6\times10^{-9}}{2.22\times10^{-22}}
\approx7.2\times10^{12}.
\]

Daarom is de juiste formulering:

\[
\boxed{
\text{De genormaliseerde body-}\Omega\text{-proxy ligt ongeveer}
7.2\times10^{12}
\text{ maal boven de veldbracket.}
}
\]

Dit is een verschil van ongeveer dertien ordes, niet zeven.

Dat ondersteunt sterk dat beide routes verschillende fysische observabelen meten.

---

## 5. Wat de ROT × MUTUAL-term werkelijk aantoont

De operationele decompositie gebruikt onder andere:

- `MUTUAL_BS`: het door de andere carrier geïnduceerde Biot–Savartveld;
- `ROT`: de globale rigid-bodyrotatie uit de least-squares-fit;
- `TRANS`: de globale translatie;
- `GEOM`: de actuele geometrie;
- `PARAM`: de actuele parameterisatie.

De grote R4-interactieterm betekent daarom primair:

\[
\boxed{
\text{Het mutuale centerline-veld projecteert vooral op de globale rigid-rotation mode.}
}
\]

Wanneer `MUTUAL_BS` wordt uitgeschakeld, bestaat de mutuale rigid-bodyrotatiecomponent vanzelfsprekend niet. Een grote `ROT × MUTUAL_BS`-interactie is dus gedeeltelijk een gevolg van de gekozen decompositiearchitectuur.

### Wat wel volgt

De andere carrier induceert hoofdzakelijk een coherente globale rotatierespons van de gehele knoop.

### Wat nog niet volgt

De term bewijst nog niet dat:

- de interne swirlfase wordt meegesleept;
- proper time wordt gemoduleerd;
- een hydrodynamische frame-draggingwet is gevonden;
- de globale rigid-bodyrotatie een interne klokfrequentie vertegenwoordigt.

Een fysisch neutralere naam is:

\[
\texttt{mutual rigid-mode occupancy}.
\]

---

## 6. Waarom \(v_{\rm def}\) geen interne swirlfase is

De huidige rigid-fit schrijft de centerline-velocity als:

\[
\mathbf v_i
=
\mathbf U
+
\boldsymbol\Omega_{\rm rigid}\times\mathbf r_i
+
\mathbf v_{{\rm def},i}.
\]

De term \(\mathbf v_{\rm def}\) is het residu van de **centerlinebeweging** nadat globale translatie en rigid-bodyrotatie zijn verwijderd.

Daarom:

\[
\boxed{
\mathbf v_{\rm def}
\neq
\mathbf v_{\rm internal\ swirl}.
}
\]

De simulator lost momenteel geen materiaalpunten op een vortexbuisdoorsnede op. Hij gebruikt een één-dimensionale centerline met \(a_{\rm sim}\) als Biot–Savartregularisatie.

Een echte interne fase vereist minimaal een lokaal materiaalframe:

\[
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2)
\]

en een fasehoek:

\[
\theta_{\rm int}(s,t)
\]

rond de lokale buisas.

De canonieke interne frequentieschaal blijft:

\[
\omega_c
=
\frac{v_{\!\circlearrowleft}^{\ast}}{r_c}.
\]

De alternatieve identificatie:

\[
\omega_c\sim\frac{v_{\!\circlearrowleft}^{\ast}}{a_{\rm core}}
\]

is niet canoniek zolang \(a_{\rm core}=r_c\) niet onafhankelijk is afgeleid.

---

## 7. Afstandsschaling

Eenvoudige a-prioriverwachtingen zoals:

\[
d^{-1},\quad d^{-2},\quad d^{-3}
\]

zijn voor gesloten vortexknopen niet automatisch geldig.

Uit de bestaande driftpunten volgt lokaal ongeveer:

\[
u_{\rm RMS}\propto d^{-2.98}.
\]

Voor de globale mutuale rigid-bodyhoeksnelheid volgt over hetzelfde kleine afstandsinterval ongeveer:

\[
|\Omega_{\rm mutual}|\propto d^{-5.75}.
\]

Deze waarden zijn slechts lokale fits over een smal interval en mogen niet als universele wetten worden beschouwd.

De correcte volgende stap is daarom een brede afstands-, oriëntatie- en multipoolbenchmark op bevroren geometrieën.

---

## 8. Resolutiegedrag en voorlopige continuümlimiet

De canonieke \(L_K\)-ratio geeft:

\[
47.526,\quad35.390,\quad31.071,\quad28.008
\]

voor:

\[
N=128,\;192,\;256,\;384.
\]

Een uitsluitend diagnostische fit:

\[
Q(N)=Q_\infty+AN^{-p}
\]

geeft ongeveer:

\[
p\approx1.98,
\qquad
Q_\infty\approx25.49.
\]

Daaruit volgen indicatief:

\[
Q_{512}\approx26.91,
\qquad
Q_{768}\approx26.13.
\]

De verwachte relatieve verandering tussen \(N=512\) en \(N=768\) is dan ongeveer:

\[
2.9\%.
\]

De 5%-convergentiegate zou daarmee waarschijnlijk slagen.

### Consequentie voor \(\kappa_{\rm geom}\)

In de continuümlimiet zou diagnostisch gelden:

\[
\kappa_\infty
\approx
\frac{1}{25.49}
\approx0.03923.
\]

De eerder opvallende kandidaten:

\[
\frac{1}{3\cdot16.371637}\approx0.02036,
\]

en:

\[
\frac{1}{\pi\cdot16.371637}\approx0.01944
\]

zijn geselecteerd op basis van de nog grove \(N=128\)-waarde.

Wanneer de resolutietrend doorzet, worden deze kandidaten niet beter maar slechter.

Daarom moet de huidige \(\kappa_{\rm geom}\)-registry worden behandeld als:

\[
\boxed{\text{EXPLORATORY · DATA-INFORMED}}
\]

in plaats van als confirmatoire no-fit-test op dezelfde trefoildataset.

---

## 9. Geherinterpreteerde fysische conclusie

### Harde simulatorconclusie

De externe carrier induceert op de andere carrier:

1. een tangentieel mutual velocity field van orde:
   \[
   10^{-11}\ {\rm m\,s^{-1}};
   \]

2. een globale mutuale rigid-bodyrotatierespons van orde:
   \[
   10^{-15}\ {\rm s^{-1}};
   \]

3. een stabiele tekenomslag onder omkering van de carrieroriëntatie;

4. een kinematische Swirl-Clock-envelope van orde:
   \[
   10^{-22};
   \]

5. een globale rigid-bodyresponseproxy van orde:
   \[
   10^{-9}.
   \]

Deze observabelen zijn reproduceerbaar binnen de simulator, maar vertegenwoordigen niet automatisch dezelfde fysische grootheid.

### Sterke Research-Track-hypothese

De mutuale interactie produceert voornamelijk een coherent rotatiemoment op de gehele knoop.

Dat kan een voorloper zijn van een interne fasekoppeling, maar alleen wanneer een werkelijk intern materiaalframe en een afgeleide faseobservable worden toegevoegd.

### Niet ondersteund

De huidige gegevens bewijzen nog niet dat:

- de R4-interactie proper time is;
- de interne Comptonfase wordt meegesleept;
- \(\kappa_{\rm geom}\) uit ropelength of crossing number volgt;
- de Kelvin-modus de klok is;
- de body-\(\Omega\)-proxy direct moet worden versterkt of verzwakt.

---

# 10. Ontwikkelroadmap

## v7.6.23 — Numerical continuum audit

### Doel

Vaststellen waar de primaire observabelen werkelijk naartoe convergeren.

### Implementatie

Voeg Richardson-analyse toe voor:

\[
u_{\rm RMS},
\quad
\Omega_{\rm mutual},
\quad
Q_{L_K},
\quad
\delta\ln R_{\rm field},
\quad
\kappa_{\rm required}.
\]

Per observable rapporteren:

- resolutiereeks;
- effectieve orde \(p\);
- continuümlimiet;
- fitresidu;
- extrapolatie-onzekerheid;
- \(N=512\rightarrow768\)-verandering.

### Correcties

- render `interactionToTotal` als `null` wanneer teller en totaal beide numeriek nul zijn;
- bewaak de R22-reachmismatch bij \(N=512\) en \(N=768\);
- label de bestaande \(\kappa_{\rm geom}\)-registry als `EXPLORATORY · DATA-INFORMED`;
- sta geen `ACCEPTED`-status toe op dezelfde dataset waarmee kandidaten zijn geselecteerd.

---

## v7.6.24 — Directed local Swirl-Clock route

### Doel

De symmetrische RMS-envelope vervangen door een gerichte lokale voorspelling.

### Definitie

Gebruik:

\[
v_{\rm eff}^2(s)
=
\left|
v_{\!\circlearrowleft}^{\ast}\hat{\mathbf e}(s)
+
\mathbf u_{\rm mutual}(s)
\right|^2.
\]

Dus:

\[
v_{\rm eff}^2(s)
=
(v_{\!\circlearrowleft}^{\ast})^2
+
2v_{\!\circlearrowleft}^{\ast}u_\parallel(s)
+
|\mathbf u_{\rm mutual}(s)|^2.
\]

Met:

\[
u_\parallel(s)
=
\mathbf u_{\rm mutual}(s)\cdot\hat{\mathbf e}(s).
\]

Daarna:

\[
\ln\eta(s)
=
\frac12
\ln\left(
1-
\frac{v_{\rm eff}^2(s)}{c^2}
\right),
\]

en arclengthgemiddelde:

\[
\langle\ln\eta\rangle_L
=
\frac{1}{L_K}
\oint_K\ln\eta(s)\,ds.
\]

### Rapportage

- signed mean \(\langle u_\parallel\rangle_L\);
- RMS van \(u_\parallel\);
- positieve bijdrage;
- negatieve bijdrage;
- lokale minima en maxima;
- A/B-pariteit;
- chiralitypariteit;
- vergelijking met de oude \(\pm u_{\rm RMS}\)-envelope.

---

## v7.6.25 — Distance, multipole and orientation benchmark

### Doel

De lokale afstands- en oriëntatieschaling rechtstreeks meten.

### Scenario’s

Gebruik bevroren geometrieën met bijvoorbeeld:

\[
d/L_K=1.1,\;1.25,\;1.5,\;2,\;3,\;4.
\]

Voeg toe:

- laterale offset;
- relatieve kantelhoek;
- co-/contraoriëntatie;
- gespiegeld trefoil;
- chiralityswap.

### Fitgrootheden

Fit afzonderlijk:

\[
u_{\rm mutual},
\quad
\Omega_{\rm mutual},
\quad
\nabla\mathbf u_{\rm mutual},
\quad
\delta\ln R_{\rm directed}.
\]

Reserveer minstens twee afstandspunten als holdout.

---

## v7.6.26 — Observable-separation cleanup

### Doel

Voorkomen dat verschillende fysische observabelen dezelfde klokterminologie gebruiken.

### Hernoemingen

- `phaseLogRatio` → `rigidResponseLogRatio`
- `omegaBody` → `omegaRigidCenterline`
- `fieldLogMin/Max` → `kinematicClockEnvelopeMin/Max`
- `v_def` → `centerlineDeformationResidual`

### UI-structuur

Maak drie strikt gescheiden blokken:

1. **KINEMATIC CLOCK**
2. **RIGID CARRIER RESPONSE**
3. **INTERNAL PHASE — NOT YET RESOLVED**

De historische body-\(\Omega\)-closure blijft als negatieve controle bestaan, maar bepaalt niet langer het primaire Research Track-verdict.

---

## v7.6.27 — Passive material-frame scaffold

### Doel

Een echte interne fasecoördinaat mogelijk maken zonder de solver te beïnvloeden.

### Frame

Voeg per centerlinepunt toe:

\[
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2).
\]

Gebruik bij voorkeur Bishop transport om kunstmatige Frenet-torsiesingulariteiten te vermijden.

### Interne fase

Definieer passief:

\[
\theta_{\rm int}(s,t).
\]

Niet-geperturbeerde frequentie:

\[
\dot\theta_0
=
\omega_c
=
\frac{v_{\!\circlearrowleft}^{\ast}}{r_c}.
\]

### Gates

- frame-orthogonaliteit;
- frame-normalisatie;
- gesloten-loop-holonomie;
- onafhankelijkheid van initiële fase;
- onafhankelijkheid van startindex;
- A/B-symmetrie;
- resolutieconvergentie;
- nul invloed op de dynamische solver.

---

## v7.6.28 — External velocity-gradient tensor

### Doel

Lokale rotatie en strain van het externe veld uit elkaar halen.

### Tensor

Bereken:

\[
G_{ij}
=
\partial_j u_{{\rm mutual},i}.
\]

Splits:

\[
S=\frac12(G+G^T),
\qquad
W=\frac12(G-G^T).
\]

Waarbij:

- \(S\): strain-rate;
- \(W\): lokale rigid rotation / vorticity.

### ENGINE-gates

- incompressibiliteit:
  \[
  \operatorname{tr}G\approx0;
  \]

- stencilconvergentie;
- resolutieconvergentie;
- A/B-pariteit;
- onafhankelijkheid van parameterisatie-index.

### Researchoutputs

\[
\hat{\mathbf t}^{T}S\hat{\mathbf t},
\]

\[
\hat{\mathbf n}_1^{T}S\hat{\mathbf n}_1,
\]

\[
\hat{\mathbf n}_2^{T}S\hat{\mathbf n}_2,
\]

\[
\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t}.
\]

Vergelijk deze met de bestaande globale \(\Omega_{\rm mutual}\)-respons.

---

## v7.6.29 — Internal-phase modulation candidates

### Voorwaarde

Pas uitvoeren wanneer het material frame en de velocity-gradienttensor technisch gevalideerd zijn.

### Route B — rotation-driven phase transport

Een mogelijke af te leiden vorm is:

\[
\delta\dot\theta_{\rm int}
=
\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t}.
\]

Deze formule mag alleen worden gebruikt wanneer zij volgt uit het gekozen frametransport, niet omdat zij numeriek sluit.

### Route C — strain/Kelvin route

Alleen bij een expliciet finite-core-profiel:

\[
\delta\omega_K
=
\mathcal F_K[S;a_{\rm core},\Gamma,k].
\]

Alle coefficienten moeten uit de hydrodynamische afleiding volgen.

De globale body-\(\Omega\)-respons blijft slechts een correlatie-observable.

---

## v7.6.30 — Confirmatory holdout benchmark

### Doel

Een volledig bevroren kandidaatwet testen op ongeziene scenario’s.

### Holdouts

- trefoil met nieuwe afstanden;
- trefoil met nieuwe oriëntaties;
- gespiegeld trefoil;
- figure-eight als achirale controle;
- minstens één tweede ideale knoop;
- meerdere \(a_{\rm sim}\)-waarden;
- meerdere resoluties;
- verschillende initiële parameterisaties.

### Acceptatiecriteria

Een kandidaat moet tegelijk slagen op:

\[
\text{continuümconvergentie},
\]

\[
\text{static-null},
\]

\[
\text{A/B-pariteit},
\]

\[
\text{chiraliteitsvoorspelling},
\]

\[
\text{afstandsholdout},
\]

\[
\text{oriëntatieholdout},
\]

\[
a_{\rm sim}\text{-onafhankelijkheid},
\]

\[
\text{coefficienten uit afleiding, niet uit fit}.
\]

---

## v7.7.0 — Beslismijlpaal

Promoveer pas naar v7.7.0 wanneer één van de volgende twee uitkomsten is bereikt:

\[
\boxed{\text{Een intern afgeleide klokobservable doorstaat alle holdouts.}}
\]

of:

\[
\boxed{\text{De onderzochte interne-klokroutes worden reproduceerbaar verworpen.}}
\]

Beide uitkomsten zijn wetenschappelijk geldig en waardevol.

---

## 11. Prioriteitenvolgorde

### Hoogste prioriteit

1. \(N=512/768\) en Richardsonanalyse;
2. signed local field route;
3. afstands- en oriëntatiebenchmark;
4. terminologische scheiding van observabelen.

### Middellange termijn

5. passief Bishop-material frame;
6. velocity-gradienttensor;
7. interne faseobservable;
8. Kelvin/strain-kandidaten.

### Pas als laatste

9. \(\kappa_{\rm geom}\)-closureclaims;
10. frame-dragginginterpretatie;
11. koppeling aan de solver;
12. eventuele canonieke promotie.

---

## 12. Eindstatus

De huidige simulator heeft overtuigend vastgesteld dat \(L_K\) de opgeloste gesloten centerline-lengte is en dat de numerical cutoff \(a_{\rm sim}\) niet als fysieke core-radius mag worden gebruikt.

De simulator heeft daarnaast een reproduceerbare globale rigid-bodyrespons en een kinematische Swirl-Clock-envelope geïdentificeerd.

Hij heeft nog niet vastgesteld dat deze observabelen een interne SST-klok of fysische tijdsdilatatie vormen.

De volgende wetenschappelijk correcte stap is daarom niet het zoeken naar een nieuwe passende coefficient, maar het construeren van een onafhankelijke interne faseobservable en een gerichte lokale interactiewet.
