# VortexLab v7.6.11 — fase-nullpatch en onderzoeksnotitie

## Versiestatus

- **Nieuwe versie:** `vortexring-lab-v7.6.11.html`
- **Parent:** v7.6.10
- **Basislijn:** v7.5.3
- **Patchklasse:** passieve diagnostiek en reproduceerbare logging
- **Solverstatus:** de filament-ODE, RK4-stapper, Biot–Savart-dynamica, topology guard, BEM en vortex-stretching gate zijn niet inhoudelijk gewijzigd.

De verhoging van **7.6.10 naar 7.6.11** is daarom een patchversie: de waargenomen fout zat in de interpretatie en numerieke uitvoering van de speculative swirl-clockdiagnose, niet in de onderliggende dynamische solver.

---

## 1. Aanleiding: sessie v7.6.10

Bronlog:

- sessie: `26f7d8d6-bc34-4bc1-9ce8-fce4f4b6edf8`
- export: 2026-07-15 03:10:24 UTC
- versie: 7.6.10

### Relevante eindinstellingen

| Instelling | Waarde |
|---|---:|
| modus | botsing |
| topologie | trefoil |
| interactie | Biot–Savart (`bs`) |
| medium | SST |
| kern | vast |
| kwaliteit | hoog |
| simulatiekernstraal \(a_{\rm sim}\) | \(1.000\times10^{-3}\ \mathrm{m}\) |
| canonieke \(R_{\rm horn}\) | \(1.40897017\times10^{-15}\ \mathrm{m}\) |
| initiële axiale afstand | \(5.000\ \mathrm{m}\) |
| laterale offset | \(0\ \mathrm{m}\) |
| drift A/B | \(+5/-5\ \mathrm{mm\,s^{-1}}\) |
| solverframe / displayframe | corot / lab |
| achtergrondstroming | bundle |
| bundelprofiel | parallel |
| \(\Omega_{\rm bundle}\) | \(1\ \mathrm{rad\,s^{-1}}\) |
| BEM | aan, `asim`, kwaliteit mid |
| topology guard | aan |
| auto-relax | uit |
| speculative clock | aan |
| visuele vergroting | \(1\times\) |

### Getoond resultaat

| Grootheid | Waarde |
|---|---:|
| canonieke geïsoleerde vertraging A/B | \(6.656441\ \mathrm{ppm}\) / \(6.656441\ \mathrm{ppm}\) |
| actuele afstand | \(4.9177\ \mathrm{m}\) |
| \(u_{\parallel,\rm RMS}\), B→A / A→B | weergegeven als \(0.0/0.0\ \mathrm{nm\,s^{-1}}\) |
| \(R_{AB}^{\rm field}\) | \(1.000000000000\ldots1.000000000000\) |
| \(\eta_A^{\rm phase}\) | \(0.999848332\) |
| \(\eta_B^{\rm phase}\) | \(0.999902940\) |
| \(R_{AB}^{\rm phase}\) | \(0.999945386110\) |
| \(\Delta\tau_{AB}^{\rm field}\) | \(0.000\ \mathrm{as}\ldots0.000\ \mathrm{as}\) |
| \(\Delta\tau_{AB}^{\rm phase}\) | \(-51.443\ \mu\mathrm{s}\) |

Uit het getoonde faseratio volgt:

\[
\ln R_{AB}^{\rm phase}
=
\ln(0.999945386110)
\approx
-5.46154\times10^{-5},
\]

oftewel een instantane proxy-asymmetrie van ongeveer

\[
(1-R_{AB}^{\rm phase})\times10^6
\approx
54.614\ \mathrm{ppm}.
\]

De laatste kalibratie in de log vond plaats bij ongeveer

\[
t_{\rm cal}=5.528246\ \mathrm{s},
\qquad
 d_{AB}=4.944705\ \mathrm{m},
\]

waarna de run doorging tot

\[
t_{\rm end}=9.882768\ \mathrm{s}.
\]

De getoonde \(-51.443\ \mu\mathrm{s}\) was dus alleen de accumulatie over ongeveer

\[
\Delta t\approx4.354522\ \mathrm{s},
\]

met een gemiddelde relatieve proxy-afwijking van circa

\[
\frac{-51.443\ \mu\mathrm{s}}{4.354522\ \mathrm{s}}
\approx
-11.814\ \mathrm{ppm}.
\]

---

## 2. Waarom v7.6.10 geen geldige klokmeting opleverde

### 2.1 Kale body-frequentie mengde meerdere effecten

v7.6.10 gebruikte

\[
\eta_i^{\rm phase}
=
\frac{|\Omega_i|}{|\Omega_{i,0}|}.
\]

Hierin zaten gelijktijdig:

- eigen Biot–Savart-rotatie van de knoop;
- gemeenschappelijke bundelrotatie;
- BEM-correctie;
- geometrische vervorming van de knoop;
- wederzijdse inductie door de andere drager.

De gewenste wederzijdse bijdrage was daardoor niet geïsoleerd.

### 2.2 Achtergrondrotatie domineerde de observable

De vroege kalibraties zonder actieve bundel lagen rond

\[
|\Omega_{\rm body}|\sim1.034\times10^{-6}\ \mathrm{rad\,s^{-1}},
\]

terwijl latere kalibraties met de bundel rond

\[
|\Omega_{\rm body}|\sim1\ \mathrm{rad\,s^{-1}}
\]

lagen. De meetroute werd dus ongeveer zes ordes van grootte door de achtergrondrotatie gedomineerd.

### 2.3 De referentie werd tijdens dezelfde sweep herhaaldelijk vervangen

De log bevat kalibraties bij onder andere

\[
t_{\rm phys}=1.065,
\ 3.375,
\ 3.557,
\ 3.677,
\ 5.528\ \mathrm{s}.
\]

Elke kalibratie zette de faseaccumulatie opnieuw op nul. Daardoor was het eindresultaat geen integraal over één vooraf vastgelegde afstandssweep.

### 2.4 De veldroute verloor sub-ulp verschillen

Bij zeer kleine \(u_{\parallel}\) werd eerst numeriek

\[
\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\pm u_{\parallel}
\]

gevormd. Wanneer \(u_{\parallel}\) kleiner is dan één floating-point-ulp van
\(\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\approx1.09\times10^6\ \mathrm{m\,s^{-1}}\), verdwijnt de perturbatie al vóór de klokfunctie wordt geëvalueerd.

Daarna werden bovendien twee getallen zeer dicht bij één van elkaar afgetrokken. Dit verklaart de ingestorte veldbracket en de exact nul getoonde accumulatie.

### 2.5 De log bevatte de zichtbare klokuitkomst niet

De v7.6.10-log registreerde instellingen, kalibratie-events en algemene diagnostiek, maar niet de volledige actuele klokwaarden. De uiteindelijke \(R_{AB}\)- en lagwaarden moesten daarom uit de UI worden overgenomen.

---

## 3. Gekozen correctie in v7.6.11

### 3.1 Momentane geïsoleerde aftrek

Voor iedere actuele geometrie worden nu twee velden per drager geëvalueerd:

\[
\Omega_i^{\rm full}
\quad\text{en}\quad
\Omega_i^{\rm iso}.
\]

`full` bevat beide dragers en dezelfde achtergrondvoorwaarden. `iso` bevat alleen de eigen drager, maar behoudt dezelfde achtergrondbundel, solverframe en overige externe voorwaarden.

De directe fase-nullgrootheid is

\[
\delta_i
=
\frac{
\Omega_i^{\rm full}-\Omega_i^{\rm iso}
}{
|\Omega_i^{\rm iso}|
}.
\]

Daarmee worden gemeenschappelijke achtergrondrotatie en eigen body-rotatie op dezelfde actuele geometrie afgetrokken.

### 3.2 Eén vergrendelde verre referentie

Bij de kalibratie worden

\[
\delta_{A,0},\qquad \delta_{B,0}
\]

vastgelegd. Daarna gebruikt de diagnose

\[
\eta_i^{\rm phase-null}
=
1+\delta_i-\delta_{i,0}.
\]

De kalibratieknop wordt vervolgens vergrendeld. Een nieuwe referentie is alleen mogelijk na een geometrische reset of een instelling die de geometrie opnieuw opbouwt.

Kalibratie na \(t>0\) wordt alleen toegestaan wanneer de simulatie is gepauzeerd.

### 3.3 Stabiele logaritmische veldbracket

De klokfunctie blijft formeel

\[
\eta(v)=\sqrt{1-v^2/c^2},
\]

maar de perturbatie wordt niet meer berekend door eerst het grote getal
\(\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}\pm u\) te vormen.

In plaats daarvan wordt de kleine correctie rechtstreeks in
\(\ln\eta\)-ruimte bepaald. Voor \(\beta_0=\mathbf{v}_{\!\boldsymbol{\circlearrowleft}}/c\) en \(d=u/c\):

\[
\Delta\ln\eta_{\pm}
=
\frac12
\ln\!\left[
1+
\frac{-(\pm2\beta_0d+d^2)}{1-\beta_0^2}
\right].
\]

De veldverhouding wordt vervolgens geëvalueerd als

\[
\Delta\ln R_{AB}^{\rm field}
=
\Delta\ln\eta_A-
\Delta\ln\eta_B.
\]

Hierdoor blijft ook een perturbatie behouden die kleiner is dan één ulp van de absolute swirl-snelheid.

### 3.4 Differentiële lagaccumulatie

v7.6.11 integreert rechtstreeks

\[
\Delta\tau_{AB}
=
\int(\eta_A-\eta_B)\,dt,
\]

waarbij het kleine verschil stabiel uit de logperturbaties wordt berekend. Er worden niet langer eerst twee bijna gelijke absolute proper-times opgebouwd en daarna afgetrokken.

Voor de fase-nullroute wordt overeenkomstig de kleine offset

\[
(\delta_A-\delta_{A,0})-(\delta_B-\delta_{B,0})
\]

geïntegreerd.

### 3.5 Uitgebreide reproduceerbare logging

Elke diagnostische logregel bevat vanaf v7.6.11 onder andere:

- kalibratietijd en kalibratieafstand;
- \(\Omega_A^{\rm full},\Omega_B^{\rm full}\);
- \(\Omega_A^{\rm iso},\Omega_B^{\rm iso}\);
- \(\Delta\Omega_A,\Delta\Omega_B\);
- stabiele veldbracket in \(\Delta\ln R\);
- fase-nullwaarde in \(\Delta\ln R\);
- proxyresidu;
- veld- en faselag;
- bundelstatus, bundelprofiel, splay en \(\Omega_{\rm bundle}\).

---

## 4. Waarom juist deze patch is gekozen

Deze patch corrigeert de drie concrete oorzaken van de v7.6.10-uitkomst zonder een nieuwe SST-wet te postuleren:

1. **Achtergrondcontaminatie:** opgelost door momentane geïsoleerde aftrek.
2. **Referentiedrift:** opgelost door één vergrendelde kalibratie.
3. **Numerieke cancellatie:** opgelost door directe perturbatie- en logruimteberekening.

Een alternatieve patch die alleen de waarschuwingstekst zou aanpassen, zou de fout zichtbaar maken maar niet oplossen. Een alternatieve patch die de faseproxy simpelweg door een handmatig gekozen schaalfactor zou delen, zou ad hoc zijn en geen falsifieerbare nulltest opleveren.

De gekozen v7.6.11-route is daarom de minimale wetenschappelijk verdedigbare correctie: zij maakt de bestaande proxy strenger en beter reproduceerbaar, zonder haar ten onrechte canoniek te verklaren.

---

## 5. Nieuwe statussemantiek

### FASE-NULLROUTE OPEN

Nog niet gekalibreerd. Pauzeer de simulator en kalibreer eenmaal bij de grootste praktische afstand.

### FASE-NULLTEST BINNEN RUWE BRACKET

De geïsoleerd afgetrokken fase-nullproxy ligt numeriek binnen de formele veldbracket. Dit is geen bevestiging of closure.

### FASEPROXY-NULLTEST MISLUKT

Na eigen- en achtergrondaftrek ligt de fase-nullproxy buiten de stabiele veldbracket. Dit verwerpt de gebruikte proxyrealisatie voor die run, maar niet een SST-parametercombinatie of SST-klokwet.

---

## 6. Aanbevolen v7.6.11-procedure

1. Start v7.6.11 en pas de swirl-clock sweep-preset toe.
2. Stel eerst alle bedoelde achtergrondvoorwaarden in, inclusief bundle/BEM.
3. Stel \(\Delta z_{AB,0}=5.000\ \mathrm{m}\), \(\Delta x=0\), en de gewenste drifts in.
4. Reset de geometrie nadat de definitieve instellingen zijn gekozen.
5. Pauzeer de simulator wanneer \(t_{\rm phys}>0\); bij \(t=0\) kan direct worden gekalibreerd.
6. Kalibreer de fase-nullreferentie precies eenmaal.
7. Controleer dat direct na kalibratie geldt:

\[
\eta_A^{\rm phase-null}=1,
\qquad
\eta_B^{\rm phase-null}=1,
\qquad
\Delta\ln R_{AB}^{\rm phase-null}=0,
\qquad
\Delta\tau_{AB}^{\rm phase-null}=0.
\]

8. Start de sweep en kalibreer niet opnieuw; de knop hoort vergrendeld te blijven.
9. Exporteer na afloop `log.txt`. De klokuitkomst staat nu rechtstreeks in de diagnostische records.

---

## 7. Minimale acceptatiecriteria

De patch is functioneel geslaagd wanneer:

- een tweede kalibratie zonder reset wordt geweigerd;
- bundelrotatie niet opnieuw een kunstmatige \(\mathcal O(10^{-5})\)-faseverhouding veroorzaakt wanneer die voor A en B gemeenschappelijk is;
- een zeer kleine niet-nul veldperturbatie zichtbaar blijft in
  \(\Delta\ln R_{AB}^{\rm field}\), ook wanneer de gewone ratio als `1.000000000000` wordt afgerond;
- A↔B-wisseling het teken van de differentiële lag omkeert maar de grootte bij een symmetrische run behoudt;
- de uitkomst convergeert bij verhoging van de ruimtelijke kwaliteit en wijziging van `sampleStride`;
- de geëxporteerde log voldoende gegevens bevat om de getoonde status achteraf te reconstrueren.

---

## 8. Wetenschappelijke grens

v7.6.11 maakt de diagnose numeriek schoner, maar leidt nog steeds geen SST-interne klokfase af. De fase-nullroute blijft een Research-Track-observable:

\[
\boxed{
\text{betere nulltest}
\neq
\text{canonieke klokwet}
}
\]

De patch kan een proxyrealisatie falsificeren wanneer zij haar eigen nulltests niet doorstaat. Zij kan op zichzelf geen SST-klokwet bevestigen.
