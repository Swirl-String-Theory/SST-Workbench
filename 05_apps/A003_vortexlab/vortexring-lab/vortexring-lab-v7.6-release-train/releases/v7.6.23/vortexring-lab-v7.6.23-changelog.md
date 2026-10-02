# VortexLab v7.6.23

Parent: `v7.6.22`  
Base lineage: `v7.5.3`  
Decomposition/export schema: `vortexlab-spec-clock-proxy-decomposition/1.7`

## Doel

V7.6.23 is een correctie- en validatierelease voor de speculatieve SST Swirl Clock-benchmarks. De versie:

1. corrigeert de foutieve conclusies van R6 en R27;
2. voegt een identiteitsbehoudende continuum-audit toe;
3. blokkeert reach-afhankelijke factoren wanneer de live thickness/DCSD-route niet convergeert;
4. exporteert benchmarkbestanden automatisch met unieke UTC-tijdstempels;
5. voegt drie onafhankelijke cross-knot-holdouts toe;
6. verandert geen solverterm en koppelt geen benchmarkuitkomst terug naar de dynamica.

De geteste Research-Track-relatie blijft:

\[
\delta\ln R_{\rm field}
=
\kappa_{\rm geom}\,
\delta\!\left(
\frac{\Omega_{\rm mutual}L_K}
{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
\right).
\]

## Gecorrigeerde R6-convergentiegate

V7.6.22 bevatte nog:

```js
if (ladder.length === 4) {
    // resolutieanalyse
}
```

terwijl de ladder inmiddels zes punten bevatte:

\[
N=128,192,256,384,512,768.
\]

Hierdoor bleef de R6-metric leeg en werd de gate kunstmatig `FAIL`.

V7.6.23 vereist en verwerkt exact de zespuntsladder. Replay op de echte v7.6.22-export geeft:

\[
\max \Delta_{512\rightarrow768}=2.8485\%<5\%,
\]

zodat de juiste conclusie is:

\[
\boxed{\mathrm{R6=PASS}.}
\]

De gate blijft uitsluitend een numerieke geldigheidstest; zij bevestigt geen klokwet.

## Gecorrigeerde R27-admissibility

V7.6.22 beoordeelde de amplitude bij de grove baseline `N=128`, maar combineerde die met de convergentie bij `N=512→768`. Daardoor konden factoren die op de grove grid dichtbij lagen als `accepted` eindigen, ook wanneer zij op hoge resolutie ongeveer een factor twee te klein waren.

V7.6.23 eist nu gelijktijdig:

- amplituderesidu bij `N=768` ≤ 10%;
- amplituderesidu in de continuümlimiet ≤ 10%;
- tijdstrajectspreiding ≤ 10%;
- `N=512→768` closure-ratioverandering ≤ 5%;
- static-null/signaal ≤ 1%;
- A/B-pariteit met tekenomslag en ≤ 10% magnitudemismatch;
- geldige diameter/radiusmetadata;
- voor reach-factoren: een convergente live reach/DCSD-route;
- voor confirmatie: onafhankelijke cross-knot-holdouts.

Replay op de v7.6.22-data geeft voor alle reeds geregistreerde factoren:

\[
\boxed{\mathrm{R27=FAIL}.}
\]

Geen factor sluit tegelijk op `N=768` en in de continuümlimiet binnen 10%.

## Identiteitsbehoudende continuum-audit

V7.6.23 past per primaire observable:

\[
X(N)=X_\infty+A N^{-p}
\]

of, wanneer de totale span ≤ 1% is, een constant model toe.

De audit omvat:

- `rigidResponseLog`;
- `mutualRawOmega`;
- `resolvedLengthRoute`;
- `fieldDeltaSigned`;
- `requiredKappa` als directe diagnostische fit;
- `mutualTangentRms`;
- `resolvedLengthA`.

De beslissende continuumwaarde van \(\kappa\) wordt niet rechtstreeks uit de ratiofit genomen, maar identiteitsbehoudend afgeleid:

\[
\boxed{
\kappa_{\infty}
=
\frac{\delta\ln R_{{\rm field},\infty}}
{\delta Q_{L,\infty}}
}.
\]

De directe ratiofit blijft zichtbaar als cross-check. Een relatieve discrepantie groter dan 10% maakt D12 ongeldig.

Replay op de v7.6.22-data geeft ongeveer:

\[
\delta Q_{L,\infty}\approx-5.8511\times10^{-22},
\]

\[
\delta\ln R_{{\rm field},\infty}
\approx-2.2908\times10^{-23},
\]

\[
\boxed{\kappa_{\infty}\approx0.03915.}
\]

Dit getal is diagnostisch en registreert geen nieuwe kandidaatfactor.

## Reach/DCSD blijft een blokkade

De stabiele centerline-lengte en de live reach-gebaseerde reconstructie lopen bij hogere resolutie uiteen. Daarom blijft R22 terecht `FAIL`.

V7.6.23 maakt het onderscheid expliciet:

- D10 bevestigt de bronconventie `D_IS_TUBE_DIAMETER`;
- R22 beoordeelt de live discrete reach/DCSD-schatter;
- een R22-fail verwerpt de Gilbert-metadata niet;
- reach-afhankelijke \(\kappa\)-factoren worden wel geblokkeerd.

De volgende roadmapstap blijft een continue doubly-critical self-distance-refinement in plaats van de huidige tolerantiegebaseerde coarse chord search.

## Cross-knot-holdouts

De runner bevat drie nieuwe scenario’s, elk bij `N=256` met checkpoints `t=0` en `t=3 s`:

1. `holdout-fseries-3_1`
   - bron: `fourier_knots_data.js`;
   - sleutel: `3_1`;
   - crossing number: 3.

2. `holdout-ideal-5_1_1`
   - bron: `ideal_knots_data.js`;
   - sleutel: `5:1:1`;
   - metadata \(L=23.598564\), \(D=1\);
   - crossing number: 5.

3. `holdout-fseries-5_1`
   - bron: `fourier_knots_data.js`;
   - sleutel: `5_1`;
   - crossing number: 5.

De volledige runner bevat nu:

- 13 scenario’s;
- 35 snapshots.

Holdouts:

- trainen of selecteren geen factor;
- rapporteren hun eigen \(L_K\), \(\delta Q_L\), veldtarget en vereiste \(\kappa\);
- evalueren alle toepasselijke vooraf geregistreerde factoren;
- kunnen alleen een universele factor bevestigen wanneer die op alle drie holdouts maximaal 10% residu heeft;
- laten metadata-afhankelijke kandidaten `N.V.T.` wanneer de benodigde metadata ontbreekt.

Nieuwe gates:

- **D12 — continuum-fit pipeline**;
- **D13 — cross-knot provenance + finite outputs**;
- **R29 — continuum audit** (`INFO`);
- **R30 — cross-knot holdout measurements** (`INFO`).

## Automatische timestamped exports

In het CLOCK-paneel staat nu standaard aangevinkt:

```text
auto-export tests met tijdstempel
```

De instelling wordt persistent opgeslagen in `localStorage`.

Na een voltooide decomposition/continuum/holdout-run worden automatisch gedownload:

```text
vortexlab-spec-clock-proxy-decomposition-7-6-23-<mode>-<UTCSTAMP>.txt
vortexlab-spec-clock-proxy-decomposition-7-6-23-<mode>-<UTCSTAMP>.json
vortexlab-spec-clock-proxy-decomposition-7-6-23-<mode>-<UTCSTAMP>.csv
vortexlab-session-7-6-23-proxy-<mode>-<UTCSTAMP>.txt
```

Na de gewone 10-runbenchmark:

```text
vortexlab-spec-clock-benchmark-7-6-23-<UTCSTAMP>.txt
vortexlab-spec-clock-benchmark-7-6-23-<UTCSTAMP>.json
vortexlab-session-7-6-23-spec-benchmark-<UTCSTAMP>.txt
```

Het tijdstempelformaat bevat UTC-datum, tijd en milliseconden, bijvoorbeeld:

```text
20260715_213045123Z
```

Browsers kunnen bij de eerste run toestemming vragen voor meerdere automatische downloads.

## Aanvullende correcties

- `interactionToTotal` wordt `null` wanneer interactie en totaal beide numeriek nul zijn; er verschijnt geen kunstmatige `10^276`-ratio meer.
- R15 heet nu expliciet een **scale-screen** en geen closuretest.
- `R23` rapporteert amplitude op `N=128`, `N=768` en continuum naast elkaar.
- `R27` gebruikt daadwerkelijke holdoutresultaten in plaats van een hardcoded blokkering.
- De interne selftest verwacht schema `/1.7`, 35 snapshots en drie aanwezige holdoutcatalogusobjecten.
- De interne selftest controleert een synthetische tweede-orde continuumreeks.
- Fseries-holdouts blijven correct gelabeld als compacte Fouriercurven en niet als ideal/tight-geometrieën.

## Niet gewijzigd

Niet inhoudelijk gewijzigd:

- RK4-integrator;
- CFL-logica;
- Biot–Savart-kern;
- topology guard;
- vortex-stretching gate;
- BEM/MFS;
- formele kinematische veldbracket;
- canonieke waarde en notatie van \(v_{\!\boldsymbol{\circlearrowleft}}^{\ast}\);
- knoopdynamica buiten de passieve benchmarkscenario’s.

## Validatie

Uitgevoerd:

- grootste inline JavaScriptblok: `node --check` PASS;
- 432 statische DOM-id’s, alle uniek;
- aanwezige catalogusobjecten:
  - fseries `3_1` PASS;
  - ideal `5:1:1` PASS;
  - fseries `5_1` PASS;
- deterministische replay tegen de echte v7.6.22 geom-\(\kappa\)-export:
  - gecorrigeerde R6 = PASS;
  - gecorrigeerde R27 = FAIL;
  - identiteitsbehoudende \(\kappa_\infty\approx0.03915\);
- automatische exportpaden en milliseconde-tijdstempel statisch geverifieerd;
- ZIP-integriteit gecontroleerd.

Niet uitgevoerd in de container:

- de volledige interactieve fysieke WebGL-run van alle 35 snapshots. De beheerde Chromium-installatie blokkeert zowel `file://` als localhost met `ERR_BLOCKED_BY_ADMINISTRATOR`.

De echte browserrun start via:

```text
RUN → 🧩 SST CLOCK · continuum + κ_geom + cross-knot holdouts
```

of via de overeenkomstige knop in het CLOCK-paneel.
