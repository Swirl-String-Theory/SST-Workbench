# VortexLab v7.6.22 — hoge-resolutie resultaatsanalyse en herziene roadmap

**Project:** SST / VortexLab  
**Versie:** 7.6.22  
**Schema:** `vortexlab-spec-clock-proxy-decomposition/1.6`  
**Analysebasis:** decomposition-run, geom-\(\kappa\)-run, SPEC CLOCK-benchmark en sessielog  
**Status:** Research Track · niet-canoniek · geen solverkoppeling  
**Datum:** 15 juli 2026

---

## 1. Executive summary

De v7.6.22-run is technisch succesvol:

\[
\boxed{\text{ENGINE=PASS}}
\]

maar het Research Track-eindverdict blijft:

\[
\boxed{\text{RESEARCH=FAIL}}
\]

De hoge-resolutieresultaten veranderen de eerdere interpretatie op vier hoofdpunten.

### 1.1 De formele veldroute is vrijwel resolutiestabiel

De gekalibreerde negatieve veldrand blijft over \(N=128\)–\(768\) rond:

\[
\delta\ln R_{\rm field}
\approx-2.29\times10^{-23}.
\]

De totale spreiding is slechts ongeveer:

\[
0.49\%.
\]

De belangrijkste resolutiedrift zit dus niet in het formele veldtarget, maar in:

\[
\delta\!\left(
\frac{\Omega_{\rm mutual}L_K}
{v_{\!\circlearrowleft}^{\ast}}
\right).
\]

### 1.2 De mutual rigid-bodyrespons convergeert, maar naar een andere amplitude

De canonieke \(L_K\)-route geeft:

\[
47.526,\ 35.393,\ 31.085,\ 28.043,\ 26.859,\ 26.203
\]

voor:

\[
N=128,\ 192,\ 256,\ 384,\ 512,\ 768.
\]

De laatste stap verandert nog:

\[
2.44\%.
\]

Een Richardson-achtige fit:

\[
Q(N)=Q_\infty+A N^{-p}
\]

geeft ongeveer:

\[
p=1.98,
\qquad
Q_\infty=25.52,
\]

en daarmee:

\[
\boxed{
\kappa_{\rm required,\infty}
\approx
\frac{1}{25.52}
=
0.03918.
}
\]

De eerdere \(N=128\)-waarde:

\[
\kappa_{\rm required}=0.02104
\]

was dus geen stabiele amplitudeschaal.

### 1.3 `R27=PASS` is een false positive in de gate-logica

Vier kandidaten worden door R27 geaccepteerd:

\[
\frac{1}{\pi\,\operatorname{Rop}_{\rm diam}},
\quad
\frac{1}{3\,\operatorname{Rop}_{\rm diam}},
\quad
\frac{1}{\pi\cdot16.371637},
\quad
\frac{1}{3\cdot16.371637}.
\]

De amplitudecontrole wordt echter uitgevoerd op de baseline bij \(N=128\), terwijl de convergentiecontrole de stap \(N=512\rightarrow768\) gebruikt.

Bij \(N=768\) zijn de overeenkomstige prediction/target-ratio’s:

| kandidaat | ratio bij \(N=128\) | ratio bij \(N=768\) |
|---|---:|---:|
| \(1/(\pi\,\operatorname{Rop}_{\rm diam})\) | 0.9247 | 0.4821 |
| \(1/(3\,\operatorname{Rop}_{\rm diam})\) | 0.9684 | 0.5049 |
| \(1/(\pi\cdot16.371637)\) | 0.9240 | 0.5095 |
| \(1/(3\cdot16.371637)\) | 0.9677 | 0.5335 |

De afwijking bedraagt bij \(N=768\) dus ongeveer:

\[
46.6\%\text{–}51.8\%,
\]

niet maximaal 10%.

De gecorrigeerde conclusie is:

\[
\boxed{\text{R27 hoort FAIL te zijn.}}
\]

### 1.4 De reach/thickness-reconstructie divergeert bij hogere \(N\)

De directe centerline-lengte blijft stabiel:

\[
0.718525\ {\rm m}
\rightarrow
0.719075\ {\rm m},
\]

een totale span van ongeveer:

\[
0.077\%.
\]

De reconstructie:

\[
L_K^{\rm reach}
=
16.371637\cdot2a_{\rm core}^{\rm reach}
\]

wijkt echter steeds sterker af:

| \(N\) | mismatch |
|---:|---:|
| 128 | 0.075% |
| 192 | 0.031% |
| 256 | 0.016% |
| 384 | 0.91% |
| 512 | 3.65% |
| 768 | 5.37% |

Daarom is:

\[
\boxed{\text{R22=FAIL}}
\]

een echte nieuwe numerieke bevinding. De huidige discrete reach/DCSD-schatter is niet geschikt als convergente fysieke \(a_{\rm core}\)-observable.

---

## 2. Bronruns en geldigheid

De sessie bevat drie relevante runs:

1. gewone 10-run SPEC CLOCK-regressie;
2. volledige decomposition-run met 29 snapshots;
3. afzonderlijke geom-\(\kappa\)-run met dezelfde 29 snapshots.

De runs zijn volledig afgerond en niet afgebroken.

### ENGINE-gates

Alle ENGINE-gates D0–D11 slagen:

- D0 snapshot-purity;
- D1 velocity-reconstruction;
- D2 mutual-linearity;
- D3 Shapley-reconstructie;
- D4 cyclic-index-invariance;
- D5 deterministic-repeat;
- D6 normalization-pipeline;
- D7 transfer-law registry;
- D8 canonieke \(v_{\!\circlearrowleft}^{\ast}\)-notatie;
- D9 lengte-route-identiteit;
- D10 ideal-knot diameter/radius-audit;
- D11 \(\kappa_{\rm geom}\)-registry.

Belangrijke numerieke marges:

\[
\epsilon_{\rm velocity}
=
5.24\times10^{-17},
\]

\[
\epsilon_{\rm raw\ \Delta\Omega}
=
1.83\times10^{-28},
\]

\[
\epsilon_{\rm length\ identity}
=
7.52\times10^{-37}.
\]

De meetpipeline zelf is dus betrouwbaar.

---

## 3. Gewone SPEC CLOCK-regressie

De gewone 10-runbenchmark blijft ongewijzigd:

\[
\boxed{\text{ENGINE=PASS}}
\qquad
\boxed{\text{RESEARCH\_PROXY=FAIL}}
\]

Geslaagde controles:

- bootstrap/CFL;
- 1×–4×–16× afspeelinvariantie;
- cilinderhoogte-invariantie;
- BEM-negatieve controle;
- nuldrift;
- A/B-tekenomslag;
- monotone drifttrend.

De closure faalt:

\[
\Delta\ln R_{\rm body}
=
-1.6000277\times10^{-9},
\]

tegen:

\[
|\Delta\ln R_{\rm field}|
=
2.2237824\times10^{-22}.
\]

Daaruit:

\[
\frac{
|\Delta\ln R_{\rm body}|
}{
|\Delta\ln R_{\rm field}|
}
=
7.195\times10^{12}.
\]

Dit bevestigt opnieuw dat de globale body-\(\Omega\)-proxy en de kinematische veldroute verschillende observabelen zijn.

---

## 4. Resolutieladder \(N=128\)–\(768\)

### 4.1 Globale rigid-bodyproxy

| \(N\) | phase/shapley total |
|---:|---:|
| 128 | \(-1.600028\times10^{-9}\) |
| 192 | \(-1.191817\times10^{-9}\) |
| 256 | \(-1.045581\times10^{-9}\) |
| 384 | \(-9.424581\times10^{-10}\) |
| 512 | \(-9.063431\times10^{-10}\) |
| 768 | \(-8.805402\times10^{-10}\) |

Relatieve veranderingen:

\[
25.51\%,
\quad
12.27\%,
\quad
9.86\%,
\quad
3.83\%,
\quad
2.85\%.
\]

De juiste R6-status is daarom:

\[
\boxed{\text{PASS}}
\]

onder de bestaande 5%-grens.

### 4.2 R6-codefout

V7.6.22 gebruikt:

```js
if (ladder.length === 4) {
    // bereken R6
}
```

maar de nieuwe ladder bevat zes punten.

Daardoor blijven:

```text
maxLastPairRelativeChange = Infinity
metrics = {}
```

en wordt R6 kunstmatig als FAIL gerapporteerd.

De voorwaarde moet worden vervangen door bijvoorbeeld:

```js
if (ladder.length >= 6) {
    // bereken volledige N=128–768-ladder
}
```

De handmatig gereconstrueerde maximale laatste-paarverandering is:

\[
2.849\%.
\]

### 4.3 Andere convergentiegates

De overige gates gebruiken de zespuntsladder correct:

| gate | status | maximale \(N=512\rightarrow768\)-verandering |
|---|---|---:|
| R8 normalisaties | PASS | 2.847% |
| R13 transferwetten | PASS | 2.844% |
| R19 lengteroutes | PASS | 4.587% |
| R26 \(\kappa\)-ratio’s | PASS | 4.194% |

De hogere resoluties bevestigen dus dat de primaire rigid-body- en transferobservabelen numeriek een plateau naderen.

---

## 5. Waar de resolutiedrift werkelijk zit

De gekalibreerde veldrand is:

| \(N\) | \(\delta\ln R_{\rm field,min}\) |
|---:|---:|
| 128 | \(-2.28728\times10^{-23}\) |
| 192 | \(-2.29085\times10^{-23}\) |
| 256 | \(-2.29007\times10^{-23}\) |
| 384 | \(-2.28889\times10^{-23}\) |
| 512 | \(-2.29848\times10^{-23}\) |
| 768 | \(-2.28904\times10^{-23}\) |

De totale relatieve span is slechts:

\[
0.49\%.
\]

Daarentegen verandert de ongecorrigeerde geometrische basis:

\[
B_N
=
\delta\!\left(
\frac{\Omega_{\rm mutual}L_K}
{v_{\!\circlearrowleft}^{\ast}}
\right)
\]

van:

\[
-1.08705\times10^{-21}
\]

naar:

\[
-5.99803\times10^{-22}.
\]

De absolute verandering over de ladder is ongeveer 45%.

De ruwe mutual rigid-body-\(\Delta\Omega\) daalt overeenkomstig:

| \(N\) | mutual raw-\(\Delta\Omega\) |
|---:|---:|
| 128 | \(-1.65487\times10^{-15}\ {\rm s^{-1}}\) |
| 192 | \(-1.23344\times10^{-15}\ {\rm s^{-1}}\) |
| 256 | \(-1.08309\times10^{-15}\ {\rm s^{-1}}\) |
| 384 | \(-9.76481\times10^{-16}\ {\rm s^{-1}}\) |
| 512 | \(-9.39119\times10^{-16}\ {\rm s^{-1}}\) |
| 768 | \(-9.12411\times10^{-16}\ {\rm s^{-1}}\) |

De lokale mutual tangent-RMS-snelheid blijft juist rond:

\[
1.83\times10^{-11}\ {\rm m\,s^{-1}}
\]

en varieert minder dan ongeveer 0.5%.

Daarom is de precieze conclusie:

\[
\boxed{
\text{de formele lokale veldroute is vrijwel geconvergeerd;}
}
\]

\[
\boxed{
\text{de resolutiedrift zit hoofdzakelijk in de globale rigid-body-\(\Omega\)-extractie.}
}
\]

Dit is fysisch relevant: het lokale Biot–Savartveld is stabieler dan de projectie daarvan op één globale rigid-rotation mode.

---

## 6. Continuümschatting van de \(L_K/v_{\!\circlearrowleft}^{\ast}\)-route

Gebruik de R26-eenheidsreeks:

\[
Q_N=
47.5261,\,
35.3934,\,
31.0854,\,
28.0433,\,
26.8588,\,
26.2033.
\]

Een fit:

\[
Q(N)=Q_\infty+A N^{-p}
\]

geeft:

\[
Q_\infty
=
25.5228\pm0.0567,
\]

\[
p
=
1.981\pm0.017.
\]

Daaruit:

\[
\boxed{
\kappa_{\rm required,\infty}
=
0.03918.
}
\]

De daadwerkelijk gemeten required-\(\kappa\)-reeks is:

| \(N\) | \(\kappa_{\rm required}\) |
|---:|---:|
| 128 | 0.021041 |
| 192 | 0.028254 |
| 256 | 0.032169 |
| 384 | 0.035659 |
| 512 | 0.037232 |
| 768 | 0.038163 |

De reeks beweegt consistent richting circa:

\[
0.0392.
\]

### Post-hocwaarschuwing

Numeriek ligt:

\[
\frac{1}{8\pi}
=
0.039789
\]

opvallend dicht bij deze continuümschatting.

Deze factor mag **niet** aan de registry worden toegevoegd enkel vanwege deze nabijheid. Dat zou post-hoc modelselectie zijn.

Hij kan uitsluitend als nieuwe kandidaat worden geregistreerd wanneer:

1. een onafhankelijke geometrische of hydrodynamische afleiding bestaat;
2. de formule vóór nieuwe runs wordt bevroren;
3. hij op ongeziene knopen, afstanden en oriëntaties wordt getest.

---

## 7. Analyse van de \(\kappa_{\rm geom}\)-kandidaten

### 7.1 R23 gebruikt alleen \(N=128\)

R23 rangschikt de kandidaten tegen:

\[
\kappa_{\rm required}(N=128)
=
0.021041.
\]

Daardoor lijkt:

\[
\frac{1}{3\operatorname{Rop}_{\rm diam}}
\]

bijna exact:

\[
\text{ratio}=0.9684.
\]

Dit is alleen een coarse-gridmatch.

### 7.2 R27 mengt verschillende resoluties

De huidige gate gebruikt:

- amplitude bij \(N=128\);
- tijdstraject bij \(N=128\);
- pariteit bij \(N=128\);
- null bij \(N=128\);
- convergentie bij \(N=512\rightarrow768\).

Dat is geen consistente confirmatoire gate.

Een kandidaat kan daardoor:

1. op de grove grid goed passen;
2. sterk naar een verkeerde amplitude convergeren;
3. toch als `accepted=true` eindigen.

### 7.3 Werkelijke high-resolutionstatus

| kandidaat | \(\kappa\) | ratio \(N=768\) | high-res residu |
|---|---:|---:|---:|
| \(1/(\pi\,\operatorname{Rop}_{\rm diam})\) | 0.019457 | 0.4821 | 51.8% |
| \(1/(3\,\operatorname{Rop}_{\rm diam})\) | 0.020376 | 0.5049 | 49.5% |
| \(1/(\pi\cdot16.371637)\) | 0.019443 | 0.5095 | 49.1% |
| \(1/(3\cdot16.371637)\) | 0.020360 | 0.5335 | 46.6% |
| \(1/(4\pi^2)\) | 0.025330 | 0.6637 | 33.6% |

Geen enkele vaste preregistreerde factor voldoet bij \(N=768\) aan de 10%-amplitudegate.

Daarom:

\[
\boxed{
\text{geen bestaande }\kappa_{\rm geom}\text{-kandidaat is high-resolution admissible.}
}
\]

### 7.4 Correcte R27-logica

Een gecorrigeerde gate moet minimaal eisen:

```text
amplitudePass = residual(N=768) <= 10%
```

of, beter:

```text
amplitudePass = residual(Richardson continuum estimate) <= 10%
```

Daarnaast:

```text
resolutionPass = last pair <= 5%
trajectoryPass = spread <= 10%
parityPass = true
nullPass = true
holdoutPass = true
```

Een kandidaat mag niet op \(N=128\) worden geselecteerd en op dezelfde dataset als confirmatoir worden geaccepteerd.

---

## 8. Radius/diameterconventie

D10 bevestigt dat de Gilbert-metadata de diameterconventie gebruikt:

\[
D\simeq2\,\operatorname{reach}.
\]

Daarom:

\[
\operatorname{Rop}_{\rm diam}
=
\frac{L}{D},
\]

en:

\[
\operatorname{Rop}_{\rm rad}
=
\frac{L}{D/2}
=
2\operatorname{Rop}_{\rm diam}.
\]

Voor de ideal trefoil:

\[
\operatorname{Rop}_{\rm diam}
=
16.371637,
\]

\[
\operatorname{Rop}_{\rm rad}
=
32.743274.
\]

De conventie-audit is geldig.

### Beperking van de trefoil-audit

Bij sample resolution 384 geeft de trefoil:

\[
2\,\operatorname{reach}
=
0.990953,
\]

tegen metadata:

\[
D=1.
\]

De fout is:

\[
0.9047\%.
\]

Dat is binnen de 1%-gate, maar aanzienlijk slechter dan de ankers \(4_1\) en \(5_1\).

De conventie is vastgesteld, maar de numerieke reach-schatter is voor de trefoil al bij \(N=384\) grensgevoelig.

---

## 9. Waarom R22 faalt

De live reach-schatter gebruikt:

\[
a_{\rm core}^{\rm reach}
=
\min
\left(
R_{\rm curvature,min},
\frac12d_{\rm approx\,DCSD}
\right).
\]

De functie `approximateDoublyCriticalDistance`:

- gebruikt een coarse index-grid;
- gebruikt een resolutieafhankelijke stride;
- accepteert een chord wanneer twee tangentprojecties kleiner zijn dan 0.22;
- voert geen continue stationaire-paaroptimalisatie uit;
- neemt vervolgens het kleinste geaccepteerde chord.

Bij hogere \(N\) worden meer chordparen getest. Een tolerantiegebaseerde bijna-orthogonale chord kan daardoor steeds kleiner worden zonder een werkelijk doubly-critical paar te zijn.

Dat veroorzaakt waarschijnlijk een neerwaartse bias in de reach.

### Benodigde vervanging

Een robuuste DCSD-pipeline moet:

1. coarse kandidaatparen zoeken;
2. kandidaatparameters \((s,t)\) continu verfijnen;
3. de voorwaarden afdwingen:
   \[
   (\gamma(s)-\gamma(t))\cdot\gamma'(s)=0,
   \]
   \[
   (\gamma(s)-\gamma(t))\cdot\gamma'(t)=0;
   \]
4. lokale-neighbourparen uitsluiten op arclengthafstand;
5. curvature- en self-distance-limiet afzonderlijk rapporteren;
6. aangeven welke term de reach bepaalt;
7. convergence onder \(N\) expliciet testen.

Tot dit is opgelost, mogen de live kandidaten:

\[
a_{\rm core}/L_K,
\qquad
2a_{\rm core}/L_K,
\qquad
1/(\pi\operatorname{Rop}_{\rm diam}),
\qquad
1/(3\operatorname{Rop}_{\rm diam})
\]

niet als betrouwbare high-resolutionfactoren worden gebruikt.

---

## 10. Status van de transfer-lawbenchmark

R15 wordt nu PASS doordat:

\[
\Delta\Omega\frac{L}{v_{\!\circlearrowleft}^{\ast}}
\]

en:

\[
\Delta\Omega\frac{d}{v_{\!\circlearrowleft}^{\ast}}
\]

bij \(N=128\) binnen de brede factor-10-schaalgate liggen en de laatste resolutiestap kleiner dan 5% is.

Dit is nuttig als screening, maar geen closure.

De gate vergelijkt een baseline-schaal en zegt alleen:

\[
0.1\leq
\frac{|T|}{|\Delta\ln R_{\rm field}|}
\leq10.
\]

Daarom moet R15 worden hernoemd naar bijvoorbeeld:

```text
transfer-law scale-screen admissibility
```

en als `INFO` of `SCREEN_PASS` worden weergegeven, niet als fysische Research Track-bevestiging.

---

## 11. Fysische herinterpretatie na v7.6.22

### 11.1 Harde conclusie

De simulator onderscheidt nu betrouwbaar:

1. het lokale mutual velocity field;
2. de globale rigid-bodyprojectie daarvan;
3. de centerline-deformatierespons;
4. de kinematische Swirl-Clockveldroute;
5. geometrische lengte- en thicknessdiagnostiek.

### 11.2 Belangrijkste nieuwe inzicht

Het lokale mutual velocity field en de veld-delta zijn vrijwel gridstabiel, terwijl de globale rigid-body-\(\Omega\)-projectie veel sterker van de filamentresolutie afhangt.

Daarom is de globale bodyrotatie geen directe lokale klokobservable.

Zij is een collectieve least-squaresrespons van de gehele centerline.

### 11.3 ROT × MUTUAL

De grote interactieterm blijft informatief:

\[
\text{ROT}\times\text{MUTUAL}
\approx
\text{volledig body-proxysignaal}.
\]

Maar hij moet worden geïnterpreteerd als:

\[
\boxed{
\text{mutual rigid-mode occupancy}
}
\]

en niet als reeds bewezen interne frame-dragging.

### 11.4 Interne fase

Een echte interne fase blijft afwezig.

Het bestaande:

\[
\mathbf v_{\rm def}
\]

is een centerline-deformatieresidu en geen azimutale stroming rond een vortexbuis.

Voor een interne klok is een passief materiaalframe nodig:

\[
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2)
\]

met:

\[
\theta_{\rm int}(s,t).
\]

---

# 12. Herziene versie-roadmap

## v7.6.23 — Gate-correctie en continuum audit

### Prioriteit 1: corrigeer de gates

1. R6:
   ```js
   ladder.length === 4
   ```
   vervangen door zespuntslogica.

2. R23:
   rapporteer afzonderlijk:
   - baseline \(N=128\);
   - high resolution \(N=768\);
   - Richardsoncontinuüm.

3. R27:
   - amplitude op \(N=768\) of continuum beoordelen;
   - geen baseline-amplitude combineren met high-res convergence;
   - holdout verplicht maken;
   - geen `PASS` op dezelfde dataset waarop kandidaten zijn gekozen.

4. Reach-afhankelijke kandidaten:
   alleen `auditPass=true` wanneer ook de live reach-convergentiegate slaagt.

5. R15:
   hernoemen naar scale-screen, niet closure/admissibility.

### Prioriteit 2: continuumrapport

Voor iedere primaire observable:

\[
X(N)=X_\infty+A N^{-p}
\]

rapporteren:

- \(X_\infty\);
- \(p\);
- fitresidu;
- fitinterval;
- leave-one-resolution-out-stabiliteit.

Observabelen:

\[
u_{\rm RMS},
\quad
\Omega_{\rm mutual},
\quad
\Delta\Omega_{\rm mutual},
\quad
Q_{L_K},
\quad
\delta\ln R_{\rm field},
\quad
\kappa_{\rm required}.
\]

### Verwachte correcte status

Na alleen gate-correctie:

- R6: PASS;
- R27: FAIL;
- R22: FAIL;
- totale Research Track-status: FAIL.

---

## v7.6.24 — Reach/DCSD solver audit

### Doel

Een convergente fysieke thickness/reach-observable construeren.

### Implementatie

- coarse chord candidate search;
- continue tweedimensionale refinement;
- exacte orthogonaliteitsresiduen;
- curvature-limit apart;
- DCSD-limit apart;
- dominant-limit flag;
- index- en arclength-exclusion;
- N=128–1536 test op statische ideal knots.

### Testknopen

- unknot;
- trefoil \(3_1\);
- figure-eight \(4_1\);
- cinquefoil \(5_1\).

### Acceptatie

\[
\frac{|D_{\rm estimated}-D_{\rm metadata}|}{D_{\rm metadata}}
<0.5\%
\]

en niet systematisch toenemend met \(N\).

---

## v7.6.25 — Directed local Swirl-Clock route

### Doel

De RMS-envelope vervangen door een lokale signed voorspelling.

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
v_{\rm eff}^2
=
(v_{\!\circlearrowleft}^{\ast})^2
+
2v_{\!\circlearrowleft}^{\ast}u_\parallel(s)
+
|\mathbf u_{\rm mutual}(s)|^2.
\]

Daaruit:

\[
\ln\eta(s)
=
\frac12
\ln\left(
1-\frac{v_{\rm eff}^2(s)}{c^2}
\right).
\]

Rapporteer:

- signed mean;
- RMS;
- positive/negative arclengthfracties;
- local extrema;
- A/B-pariteit;
- chiralitypariteit;
- vergelijking met de oude envelope.

---

## v7.6.26 — Distance, orientation and multipole benchmark

Gebruik statische/bevroren geometrieën met:

\[
d/L_K=
1.1,\ 1.25,\ 1.5,\ 2,\ 3,\ 4.
\]

Voeg toe:

- laterale offsets;
- kantelhoeken;
- co-/contraoriëntatie;
- gespiegeld trefoil;
- achirale figure-eight.

Meet afzonderlijk:

\[
u_{\rm mutual},
\quad
\Omega_{\rm rigid},
\quad
\nabla\mathbf u_{\rm mutual},
\quad
\delta\ln R_{\rm directed}.
\]

Reserveer ongeziene afstanden als holdout.

---

## v7.6.27 — Observable-separation cleanup

Hernoem:

- `phaseLogRatio`
  \[
  \rightarrow
  \texttt{rigidResponseLogRatio}
  \]

- `omegaBody`
  \[
  \rightarrow
  \texttt{omegaRigidCenterline}
  \]

- `fieldLogMin/Max`
  \[
  \rightarrow
  \texttt{kinematicClockEnvelopeMin/Max}
  \]

- `v_def`
  \[
  \rightarrow
  \texttt{centerlineDeformationResidual}
  \]

UI-blokken:

1. **KINEMATIC CLOCK**
2. **RIGID CARRIER RESPONSE**
3. **GEOMETRIC THICKNESS**
4. **INTERNAL PHASE — NOT YET RESOLVED**

---

## v7.6.28 — Passive material frame

Voeg per centerlinepunt een Bishop-frame toe:

\[
(\hat{\mathbf t},\hat{\mathbf n}_1,\hat{\mathbf n}_2).
\]

Definieer passief:

\[
\theta_{\rm int}(s,t),
\]

met ongestoorde frequentie:

\[
\dot{\theta}_0
=
\omega_c
=
\frac{v_{\!\circlearrowleft}^{\ast}}{r_c}.
\]

Nog geen externe modulatie.

Gates:

- orthogonaliteit;
- norm;
- gesloten-loop-holonomie;
- initial-phase-invariantie;
- cyclic-index-invariantie;
- resolutieconvergentie;
- nul solverfeedback.

---

## v7.6.29 — External velocity-gradient tensor

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

Controleer:

\[
\operatorname{tr}G\approx0.
\]

Rapporteer lokale projecties:

\[
\hat{\mathbf t}^TS\hat{\mathbf t},
\]

\[
\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t},
\]

en hun correlatie met de globale rigid-bodyrespons.

---

## v7.6.30 — Afgeleide interne-fasekandidaten

Pas na validatie van het materiaalframe en de gradienttensor.

### Rotatieroute

Een mogelijke afleidbare vorm:

\[
\delta\dot{\theta}_{\rm int}
=
\boldsymbol\omega_{\rm ext}\cdot\hat{\mathbf t}.
\]

### Kelvin/strainroute

Alleen met een expliciet finite-core-profiel:

\[
\delta\omega_K
=
\mathcal F_K
\left(
S,a_{\rm core},\Gamma,k
\right).
\]

Geen coefficient mag uit de v7.6.22-amplitude worden gekozen.

---

## v7.7.0 — Confirmatory milestone

Promoveer pas wanneer een bevroren wet slaagt op:

- continuümconvergentie;
- static null;
- A/B-pariteit;
- chiraliteit;
- afstandsholdouts;
- oriëntatieholdouts;
- meerdere knooptypen;
- \(a_{\rm sim}\)-onafhankelijkheid;
- independently derived coefficients.

Geldige einduitkomsten:

\[
\boxed{
\text{een interne klokwet doorstaat alle holdouts}
}
\]

of:

\[
\boxed{
\text{de geteste interne klokroutes worden reproduceerbaar verworpen}.
}
\]

---

## 13. Definitieve conclusie

V7.6.22 bevestigt dat de simulator numeriek rijp genoeg is om lokale velden en globale rigid-bodyresponsen afzonderlijk te onderzoeken.

De run ondersteunt niet dat een van de huidige \(\kappa_{\rm geom}\)-factoren de klokwet sluit.

De high-resolutiondata tonen juist:

\[
\boxed{
\kappa_{\rm required}
\text{ beweegt van }0.0210
\text{ naar ongeveer }0.0392.
}
\]

De vier door R27 geaccepteerde kandidaten zijn een gate-artefact van de combinatie:

\[
\text{coarse-grid amplitude}
+
\text{high-resolution convergence}.
\]

De eerste volgende versie moet daarom geen nieuwe fysicafactor toevoegen.

De correcte volgorde is:

\[
\boxed{
\text{gatecorrectie}
\rightarrow
\text{continuümaudit}
\rightarrow
\text{reachsolver}
\rightarrow
\text{gerichte lokale veldroute}
\rightarrow
\text{material frame}
\rightarrow
\text{interne fase}.
}
\]
