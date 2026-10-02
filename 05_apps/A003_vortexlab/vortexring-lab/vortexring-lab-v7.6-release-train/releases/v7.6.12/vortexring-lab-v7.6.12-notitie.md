# VortexLab v7.6.12 — integratorbootstrap, veilige SPEC CLOCK-start en regressienotitie

## Versiestatus

- **Nieuwe versie:** `vortexring-lab-v7.6.12.html`
- **Parent:** v7.6.11
- **Basislijn:** v7.5.3
- **Patchklasse:** numerieke integrator- en bedieningsregressie
- **Modelstatus:** de Biot–Savart-wet, LIA-term, kernmodellen, topology guard, BEM, vortex-stretching gate en de v7.6.11 fase-nullformule zijn niet inhoudelijk vervangen.
- **Waarom patchversie:** de fout zat in de eerste tijdstap, het playback-debet en de presetstatus. Er is geen nieuwe SST-klokwet of nieuwe fysische interactieterm toegevoegd.

---

## 1. Aanleiding: sessie v7.6.11

Bronlog:

- sessie: `ac7ca6ee-db68-4a72-955f-13d0b2c6f0d3`
- versie: v7.6.11
- export: 2026-07-15 03:49:29 UTC

### Relevante instellingen

| Instelling | Waarde |
|---|---:|
| modus | botsing |
| topologie | trefoil |
| medium | SST |
| interactie | Biot–Savart (`bs`) |
| kwaliteit | hoog |
| simulatiekernstraal \(a_{\rm sim}\) | \(1.000\ \mathrm{mm}\) |
| initiële axiale afstand \(\Delta z_{AB,0}\) | \(0.840\ \mathrm{m}\) |
| initiële drift A/B | \(+5/-5\ \mathrm{mm\,s^{-1}}\) |
| latere drift A/B | \(-5/+5\ \mathrm{mm\,s^{-1}}\) |
| bundelveld | uit |
| BEM-schakelaar | aan, maar zonder actief bundelveld |
| topology guard | aan |
| auto-relax | uit |
| SPEC CLOCK | aan |
| uiteindelijke afspeelparameter | `accExp=5.05` |
| uiteindelijke fase-nullkalibratie | \(t=935.233843\ \mathrm{s}\) |
| kalibratieafstand | \(1.779429\ \mathrm{m}\) |
| einde log | \(t=975.654683\ \mathrm{s}\) |

De snelle weergave meldde later onder meer:

\[
d_{AB}=2.1836\ \mathrm{m},
\qquad
d_{\rm clearance}=5.599\ \mathrm{mm},
\]

met status:

> FASEPROXY-NULLTEST MISLUKT.

Deze status is voor deze sessie niet bruikbaar als onafhankelijke proxytest, omdat de run vóór de kalibratie al door een foutieve eerste tijdstap van ongeveer negenhonderd seconden was gegaan.

---

## 2. Waargenomen regressie

### 2.1 De toestand bleef zichtbaar op \(t_{\rm phys}=0\)

Na het activeren van de preset en de eerste kalibratie bleef de log gedurende vele diagnostische samples exact op

\[
t_{\rm phys}=0.
\]

De simulatie was niet gecrasht. De deterministic stepper wachtte totdat het playback-debet groot genoeg was voor één volledige, foutief zeer grote eerste CFL-stap.

### 2.2 De eerste geaccepteerde stap was circa \(896.12\ \mathrm{s}\)

De eerste niet-nulle diagnostische toestand in de log was:

\[
t_{\rm phys}=896.1205288965\ \mathrm{s}.
\]

Dit was praktisch één bootstrapstap. De latere resets produceerden opnieuw sprongen van dezelfde orde, onder meer rond \(897.6\), \(920.6\) en \(935.2\ \mathrm{s}\).

### 2.3 Een hoge afspeelsnelheid leek de simulator te “starten”

De afspeelsnelheid verandert niet rechtstreeks de fysische stapgrootte. Zij vult alleen het tijdsdebet:

\[
D_{n+1}=D_n+A\,\Delta t_{\rm real},
\qquad
A=10^{\mathrm{accExp}}.
\]

Bij lage \(A\) duurde het zeer lang voordat

\[
D\geq \Delta t_{\rm CFL}^{(0)}
\]

werd bereikt. Bij `accExp=5.05` werd hetzelfde enorme debet vrijwel onmiddellijk gevuld, waarna de volledige stap van honderden seconden ineens werd uitgevoerd. Daarom leek het alsof de snelheidsregelaar de simulatie activeerde.

### 2.4 De preset erfde een gevaarlijk hoge afspeelsnelheid

`applySpecClockPreset()` zette in v7.6.11 geen expliciete `accExp`. Na een eerdere handmatige verhoging bleef bijvoorbeeld

\[
\mathrm{accExp}=5.05,
\qquad
A=10^{5.05}\approx1.122\times10^5
\]

actief na Reset en na het opnieuw kiezen van de SPEC CLOCK-preset. Daardoor kon een nieuwe sweep in fracties van een seconde voorbijgaan.

---

## 3. Technische hoofdoorzaak

De v7.6.11-CFL-regel bevatte onder meer:

\[
\Delta t
\leq
\frac{0.25\,\ell_{\min}}{\max(10^{-12},u_{\rm last})}.
\]

Direct na Reset werd echter gezet:

\[
u_{\rm last}=10^{-9}\ \mathrm{m\,s^{-1}}.
\]

De opgelegde driftsnelheden

\[
|v_{z,A}|=|v_{z,B}|=5\times10^{-3}\ \mathrm{m\,s^{-1}}
\]

werden pas tijdens de eerste RK4-evaluatie in het snelheidsveld opgenomen. Zij begrensden dus niet de stap die juist vóór die eerste RK4-evaluatie werd gekozen.

De local-induction/CFL-termen konden daardoor een eerste stap van orde

\[
\Delta t_{\rm CFL}^{(0)}\sim 9\times10^2\ \mathrm{s}
\]

toestaan.

---

## 4. Correctie in v7.6.12

### 4.1 Opgelegde drift begrenst de eerste stap

Er is een vooraf bekende kinematische snelheidsgrens toegevoegd:

\[
u_{\rm kin}
=
\max\!\left(
|v_{z,A}|,
|v_{z,B}|,
|w_{\rm ext}|,
u_{\rm Taylor,max}
\right).
\]

De verplaatsings-CFL gebruikt nu:

\[
u_{\rm bound}
=
\max\!\left(
10^{-12},
u_{\rm last},
u_{\rm kin}
\right),
\]

en

\[
\Delta t
\leq
\frac{0.25\,\ell_{\min}}{u_{\rm bound}}.
\]

De ingestelde \(5\ \mathrm{mm\,s^{-1}}\) is daardoor al vóór de eerste RK4-stap bekend.

### 4.2 Playback-onafhankelijke tijdstapcap

Naast de gewone ruimtelijke en dynamische CFL-voorwaarden geldt nu:

\[
\Delta t_{\max}
=
\begin{cases}
0.05\ \mathrm{s}, & \text{SPEC CLOCK actief},\\[4pt]
0.25\ \mathrm{s}, & \text{overige runs}.
\end{cases}
\]

Daarmee kan de eerste SPEC CLOCK-stap nooit opnieuw honderden seconden groot zijn. De cap hangt niet af van de afspeelsnelheid en verandert dus niet wanneer de gebruiker de snelheidsregelaar bedient.

### 4.3 Geen achterstallige playback-inhaalstap

Een wijziging van:

- afspeelsnelheid;
- pauze/hervatten;
- \(v_{z,A}\);
- \(v_{z,B}\);
- de benader-/verwijderknoppen;

wist uitsluitend het onafgewerkte playback-debet:

\[
D\rightarrow0.
\]

De fysieke toestand \(Y\), de fase-nullreferentie en de reeds geaccepteerde tijd blijven onaangetast. Er kan daardoor geen oud debet onder een nieuwe instelling als plotselinge inhaalstap worden vrijgegeven.

### 4.4 Reproduceerbare SPEC CLOCK-workflow

De SPEC CLOCK-preset doet nu expliciet:

1. `accExp=0`, dus \(1\times\);
2. Reset van de geometrie en alle klokaccumulatoren;
3. pauzeren bij exact \(t=0\);
4. armeren van één fase-nullkalibratie;
5. automatisch starten op \(1\times\) zodra de kalibratie slaagt.

De kalibratieknop toont in deze toestand:

> Kalibreer fase-nullreferentie en start 1×.

Ook een handmatige Reset terwijl SPEC CLOCK actief is, keert terug naar deze veilige toestand.

### 4.5 Uitgebreide logging

Nieuwe logvelden omvatten:

- `paused`;
- `stepDebt`;
- `dtCFL`;
- `acceptedStepTimeCap`;
- `prescribedKinematicSpeedBound`;
- `playbackDebtResetReason`.

Hiermee is achteraf direct zichtbaar of een run met de bedoelde eerste-stapgrens en veilige playbackstatus is gestart.

---

## 5. Verwacht gedrag van v7.6.12

Na het kiezen van de SPEC CLOCK-preset:

\[
t_{\rm phys}=0,
\qquad
A=1,
\qquad
\text{paused}=\text{true}.
\]

Na één klik op de kalibratieknop:

\[
\Delta t_{\rm eerste}\leq0.05\ \mathrm{s},
\]

en de sweep start automatisch. Er hoort geen lange stilstand op \(t=0\) en geen sprong naar \(t\sim900\ \mathrm{s}\) meer op te treden.

Bij relatieve axiale drift

\[
|v_{z,B}-v_{z,A}|=10\ \mathrm{mm\,s^{-1}},
\]

verloopt een meterschaal-sweep opnieuw over tientallen seconden fysische tijd, in plaats van in één bootstrapstap.

---

## 6. Interpretatie van het eerdere resultaat

De melding

> FASEPROXY-NULLTEST MISLUKT

uit de v7.6.11-sessie wordt niet overgenomen als geldige negatieve uitkomst. De referentie werd pas gezet bij

\[
t_{\rm cal}=935.233843\ \mathrm{s},
\]

nadat de geometrie reeds door foutieve reuzenstappen was geëvolueerd.

v7.6.12 verandert de fase-nullformule uit v7.6.11 niet. De nieuwe versie maakt uitsluitend de numerieke sweep reproduceerbaar. De proxy kan in een correcte nieuwe run nog steeds binnen of buiten de veldbracket vallen; pas die nieuwe run is interpreteerbaar als test van de huidige proxyrealisatie.

---

## 7. Minimale regressietest

1. Open v7.6.12.
2. Kies `SPEC CLOCK sweep`.
3. Controleer:
   - snelheid \(1\times\);
   - `Hervat` op de pauzeknop;
   - \(t_{\rm phys}=0\);
   - kalibratieknop vermeldt automatisch starten.
4. Klik eenmaal op kalibreren.
5. Controleer in de log:
   - `prescribedKinematicSpeedBound = 0.005`;
   - `acceptedStepTimeCap = 0.05`;
   - eerste niet-nulle \(t_{\rm phys}\leq0.05\ \mathrm{s}\), behoudens een kleinere topology/contactstap;
   - geen eerste sprong van honderden seconden.
6. Verander tijdens de run de afspeelsnelheid.
7. Controleer dat de toestand vloeiend verdergaat zonder inhaalstap.
8. Exporteer de log vóór een eventuele statusinterpretatie.

---

## 8. Patchmotivatie

De versie wordt **v7.6.12** en niet v7.7:

- geen nieuw fysisch model;
- geen nieuwe topologie;
- geen nieuwe canonieke SST-relatie;
- geen gewijzigde fase-nullproxy;
- wel een afgebakende numerieke regressiefix voor initialisatie, tijdstapresolutie, playback-debet en reproduceerbare presetbediening.

De patch is noodzakelijk omdat v7.6.11 technisch kon draaien, maar de eerste geaccepteerde stap en de geërfde afspeelsnelheid de bedoelde kloktest ongeldig maakten.
