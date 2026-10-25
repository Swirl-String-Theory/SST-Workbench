# VortexLab v7.6.22

Parent: `v7.6.21`  
Base lineage: `v7.5.3`  
Decomposition/export schema: `vortexlab-spec-clock-proxy-decomposition/1.6`

## Doel

Deze versie voert twee samenhangende upgrades uit:

1. de volledige speculatieve SST Swirl Clock krijgt een afzonderlijk rechter zijpaneel tussen **KERN** en **DIAG**, met compacte, afzonderlijk inklapbare benchmarkblokken;
2. de lengte-identificatiebenchmark wordt uitgebreid tot de gerichte no-fit test

\[
\delta\ln R_{\rm field}
=
\kappa_{\rm geom}\,
\delta\!\left(
\frac{\Omega_{\rm mutual}L_K}
{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}}
\right).
\]

Geen van deze diagnostieken wordt naar de solver teruggekoppeld.

## UI: zelfstandig CLOCK-paneel

De rechter dock bestaat nu uit drie onafhankelijk te openen panelen, van het canvas naar buiten:

1. **KERN**
2. **CLOCK**
3. **DIAG**

De volledige `specClockPanel` is uit DIAG gehaald en ondergebracht in **SST · SWIRL CLOCK**. Het paneel behoudt alle oorspronkelijke controls, exports, quick-controls en waarschuwingen.

Binnen CLOCK zijn zes persistente accordions aanwezig:

- geautomatiseerde SPEC CLOCK 10-run regressie;
- gecombineerde diagnosebenchmark;
- normalisatiebenchmark;
- transfer-lawregister;
- `L/v↺*`-lengte-identificatie;
- `κ_geom` plus ideal-data-conventie-audit.

De accordions hebben deterministische id’s en bewaren hun open/dicht-status via de bestaande `localStorage`-persistentie.

## Nieuwe κ_geom-benchmark

De primaire grootheid is de reeds gekalibreerde canonieke dragerroute:

\[
Q_K(t)
=
\frac{
\Omega_{{\rm mutual},A}(t)L_{K,A}(t)
-
\Omega_{{\rm mutual},B}(t)L_{K,B}(t)
}
{v_{\!\boldsymbol{\circlearrowleft}}^{\ast}},
\]

\[
\delta Q_K(t)=Q_K(t)-Q_K(0).
\]

De benchmark vergelijkt uitsluitend gelijksoortige gekalibreerde grootheden:

\[
\delta\ln R_{\rm field}(t)
\quad\text{tegen}\quad
\kappa_{\rm geom}\,\delta Q_K(t).
\]

De diagnostisch vereiste waarde

\[
\kappa_{\rm required}
=
\frac{\delta\ln R_{\rm field}}{\delta Q_K}
\]

wordt wel geëxporteerd, maar nooit als gain of fitcoëfficiënt toegepast.

### Vooraf geregistreerde kandidaten

Alle kandidaten zijn dimensieloos en hebben een vaste buitenste coëfficiënt `1`:

- `UNITY`: \(1\)
- `INV_2PI`: \(1/(2\pi)\)
- `INV_4PI`: \(1/(4\pi)\)
- `INV_4PI2`: \(1/(4\pi^2)\)
- `REACH_OVER_LK`: \(a_{\rm core}/L_K\)
- `DIAMETER_OVER_LK`: \(2a_{\rm core}/L_K\)
- `INV_PI_ROP_DIAM`: \(1/(\pi\,\mathrm{Rop}_{\rm diam})\)
- `INV_CROSSING_ROP_DIAM`: \(1/(3\,\mathrm{Rop}_{\rm diam})\)
- `INV_2PI_ROP_DIAM`: \(1/(2\pi\,\mathrm{Rop}_{\rm diam})\)
- `INV_IDEAL_PI_ROP_DIAM`: \(1/(\pi\cdot16.371637)\)
- `INV_IDEAL_CROSSING_ROP_DIAM`: \(1/(3\cdot16.371637)\)

De trefoil crossing number `3` en Gilbert-ropelength `16.371637` zijn vooraf vastgelegd; er wordt niet gezocht naar een continue optimale factor.

## Resolutieladder N=512 en N=768

De scenario’s zijn uitgebreid met:

- `resolution-512`, checkpoints \(t=0,3\ \mathrm{s}\);
- `resolution-768`, checkpoints \(t=0,3\ \mathrm{s}\).

De volledige runner bevat nu tien scenario’s en 29 snapshots:

- baseline N128: 5;
- static-null N128: 5;
- A/B-swap N128: 5;
- N192, N256, N384, N512 en N768: elk 2;
- `a_sim=0.5 mm` en `a_sim=1.5 mm`: elk 2.

Alle resolutietabellen tonen voortaan N128, N192, N256, N384, N512 en N768. De beslissende laatste-stapgate gebruikt gemeten **N512→N768**, niet langer N256→N384 of een extrapolatie.

## Nieuwe gates

### ENGINE

- **D10 — ideal-knot radius/diameter convention audit**  
  Controleert geladen bronmetadata, componentlengte, gesamplede booglengte en numerieke reach voor drie niet-triviale Gilbert-ankers.

- **D11 — κ_geom registry**  
  Vereist elf dimensieloze, coefficient-1 en eindige kandidaten voor iedere snapshot.

### RESEARCH

- **R23 — κ_geom amplitude ranking**
- **R24 — tijdstrajectproportionaliteit**
- **R25 — A/B-pariteit plus static-null**
- **R26 — closure-ratio-convergentie N128–768**
- **R27 — gecombineerde no-fit admissibility**
- **R28 — radius/diameterconsequentie**

Een kandidaat wordt alleen toegelaten wanneer tegelijk geldt:

- amplitude-residu ≤ 10%;
- ratio-spreiding over \(t=0.5,1,2,3\ \mathrm{s}\) ≤ 10%;
- verandering van de closure-ratio N512→N768 ≤ 5%;
- static-null/signaal ≤ 1%;
- A/B-magnitudemismatch ≤ 10% met tekenomslag;
- ideal-data-conventie-audit PASS.

Een RESEARCH PASS blijft diagnostisch en canoniseert geen klokwet.

## Expliciete radius/diameter-audit

`ideal_knots_data.js` bevat voor de ideale trefoil `3:1:1`:

- \(L=16.371637\);
- \(D=1.0\).

V7.6.22 controleert bij N=384 de niet-triviale ankers `3:1:1`, `4:1:1` en `5:1:1`. De audit vereist:

\[
D\simeq2\,\operatorname{reach}(\gamma),
\]

zodat:

\[
\operatorname{Rop}_{\rm diam}=\frac{L}{D},
\qquad
\operatorname{Rop}_{\rm rad}=\frac{L}{D/2}=2\operatorname{Rop}_{\rm diam}.
\]

Voor de trefoil wordt daarom expliciet geëxporteerd:

\[
\operatorname{Rop}_{\rm diam}=16.371637,
\qquad
\operatorname{Rop}_{\rm rad}=32.743274.
\]

De audit maakt de factor-tweeconventie zichtbaar; hij identificeert `a_sim` niet met de fysieke core radius.

## Preflight op de v7.6.21-uitkomst

De vorige run gaf diagnostisch ongeveer:

\[
\kappa_{\rm required}\approx0.0210411.
\]

Twee vooraf geregistreerde Gilbert-kandidaten liggen daardoor zonder fit dichtbij:

\[
\frac{1}{3\cdot16.371637}
=0.0203604,
\]

met circa 3.23% amplitude-residu, en

\[
\frac{1}{\pi\cdot16.371637}
=0.0194428,
\]

met circa 7.60% amplitude-residu.

Dit is uitsluitend een preflight. De v7.6.22-browserrun moet nog bepalen of tijdstraject, null, pariteit en vooral N512→N768-convergentie tegelijk slagen.

## Correcties en regressiebeveiliging

- De quaternion power-iteration gebruikte bij de rij-norm per abuis zes indices voor een 4×4 Davenport-matrix. De rijset is gecorrigeerd van `[0,1,2,3,4,5]` naar `[0,1,2,3]`.
- De focus-safe quick-controltest opent tijdens de test tijdelijk zowel het CLOCK-dock als het interne Swirl Clock-detailsblok. Hiermee blijft de test geldig na de UI-verplaatsing.
- De provenance-selftest negeert terecht de waarschuwingsbadge `NIET CANON` bij het zoeken naar positieve `CANON v0.8.20`-tags.
- Benchmarkverdictpersistentie verwacht nu 29 snapshots.

De filamentdynamica, Biot–Savart-kern, RK4-stappen, CFL-regel, topology guard, BEM, formele veldbracket en bestaande tien-runbenchmark zijn niet inhoudelijk gewijzigd.

## Validatie

Uitgevoerd:

- inline JavaScript: `node --check` PASS;
- 429 statische DOM-id’s, alle uniek;
- vijf onafhankelijke docktabs aangetroffen: INFO, FLOW, KERN, CLOCK, DIAG;
- CLOCK-parent in runtime: `vl-right-clock`;
- zes benchmarkaccordions met deterministische id’s;
- ideal-data-audit: PASS voor `3:1:1`, `4:1:1`, `5:1:1`;
- runtime zonder JavaScript-excepties in headless Chromium met een renderer-stub;
- volledig ingebouwd regressieharnas: **ZELFTEST 7.6.22 — GESLAAGD**.

De renderer-stub is uitsluitend voor container-validatie gebruikt en staat niet in het geleverde HTML-bestand.

Niet uitgevoerd in de container:

- de volledige fysieke WebGL-benchmark tot N=768. Deze run moet in de browser worden gestart via **RUN → 🧩 SST CLOCK · κ_geom + N768 benchmark** of via de knop in het κ_geom-blok.
