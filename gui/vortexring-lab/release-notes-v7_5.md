# Release notes v7.5 — frames ontvlochten (volledige v7.4b-scope)

**Basis:** v7.4.2 incl. d34-besluitacties D3/D4. **Bestand:** `vortexring-lab-v7_5.html`. **Naamkeuze:** spec §B.7 liet '7.4b' of '7.5.0-pre' open; op verzoek van Omar is de afgeronde v7.4b-scope uitgeleverd als **v7.5** (`APP_VERSION='7.5'`, `APP_BASE_VERSION='7.4.2'`). De v7.5.x-nummering uit plan v7 (lift-falsificatie enz.) sluit hier gewoon op aan.

## Wijzigingen (spec §B.1–B.7)

1. **Frame-ontvlechting (§B.1).** `P.solverFrame` ('lab'|'corot'), `P.displayFrame` ('lab'|'corot') en `P.bgFlow` ('none'|'wall'|'bundle') vervangen de dubbele rol van de oude frame-toggle. De identifiers `coRot`, `bgOmegaCoupling` en `bundleFlowCoupling` zijn volledig geretireerd (0 voorkomens; de validator verbiedt ze). De Ω_wall×bundel-exclusiviteit is nu een type-invariant van de bgFlow-enum in plaats van een runtime-guard. De wandadvectie u_bg=Ω×r staat uitsluitend bij `solverFrame='lab'` + `bgFlow='wall'` in het snelheidsveld; de wrijvings-v_n volgt hetzelfde predicaat (§B.1, oude mfRot-logica). Weergavetransformatie: `filGrp` roteert volgens (displayFrame − solverFrame), d.w.z. lab = R(+φ)·corot; alle vier de combinaties zijn correct afgedekt, inclusief de voorheen onbereikbare stand lab-solver + corot-display. ModelLog logt de drie velden apart in elke P-snapshot.
2. **Zelftest-T8 · frame-equivalentie (§B.2).** Geperturbeerde ring (N=96, ε=0.05, m=5), 24 LIA-stappen met externe termen, Ω=0.7, dt=min(½·dt_CFL, 0.05/Ω); corot-resultaat teruggeroteerd over φ=Ω·t en knooppuntsgewijs vergeleken. Gemeten in de node-spiegel: **E_frame = 6.6·10⁻⁸** bij φ=1.20 rad — ruim onder de 10⁻⁶-drempel. T9b-gedrag (bgFlow-invariantie) is in de node-regressie uitgebreid: corot+'wall' en lab+'none' zijn bewezen termloos en bit-identiek aan 'none'.
3. **ε_rev op gebruikersactie (§B.3).** HUD-rij `rowEpsRev` met knop "meet": 16 CFL-stappen heen + terug op een **kopie** van de actuele toestand met de werkelijk geconfigureerde dynamica (volledige externe termen, huidige interactiekern); relatieve L2-fout over de niet-ghost-filamenten; resultaat naar HUD én ModelLog (`eps-rev`-event). Expliciet 2× rekenwerk, nooit per frame. Bij α≠0 toont de rij '— (α≠0)' met de bestaande antidissipatie-waarschuwing. Momentopname wordt ook genomen bij het inschakelen van achterwaarts integreren. tPhys wordt tijdens de meting niet geadvanceerd: een eventueel tijdsafhankelijke w (Taylor-oscillatie) is bevroren — een tijdsafhankelijke aandrijving zou exacte omkeerbaarheid hoe dan ook breken.
4. **g_a = d_min/a (§B.4).** HUD-rij `rowGa`, gevoed uit het bestaande 12-frame-stabiliteitsrapport (`gapRatio`; `minGap` wordt nu mee-geëxporteerd) — géén extra O(N²) per HUD-tick. Exponentieel formaat bij g_a > 10⁶ (SST-schaal), '∞' zolang er geen rapport is.
5. **T1b N-sweep (§B.5).** Ringsnelheid bij N=96/192/384. **Eerlijke afwijking van de spec-acceptatie, met meting als grond:** de fout t.o.v. de Kelvin-asymptoot daalt niet monotoon omdat hij bij ~6.5·10⁻⁵ op de C0-kalibratievloer stuit (gemeten: U_∞ − Kelvin ≈ −7.6·10⁻⁵ relatief bij a/R≈1.8·10⁻³; de foutreeks vs Kelvin is 1.24·10⁻⁴ → 6.49·10⁻⁵ → 6.72·10⁻⁵, een tekenpassage door de vloer). Monotonie wordt daarom getest tegen een N=1536-zelfconvergentiereferentie (gemeten: 4.97·10⁻⁵ → 9.4·10⁻⁶ → 7.1·10⁻⁶, monotoon), en de spec-drempel |U(384)−Kelvin|/Kelvin < 10⁻⁴ blijft ongewijzigd staan en wordt gehaald (6.7·10⁻⁵). De motivering staat als commentaar bij de test zelf.
6. **D3/D4-acties (§B.6).** De d34-slice zat al in de basis; nieuw is zelftest-**T0i**: de bij scriptparse bevroren opstartdefaults (`P_DEFAULTS`) bewijzen dat een verse start `coreFlowLock=false` heeft en frames corot/corot/none.
7. **Provenance (§B.7).** `APP_VERSION='7.5'`, base '7.4.2', meta/title/footnote/patchnotes bijgewerkt; T0 controleert de nieuwe waarden. Validator-variant `validate-v7_5.py`: nieuwe markers (solverFrame-defaults, predicaatfuncties, rowEpsRev/rowGa, T8/T1b/T0i, ModelLog-velden, PKEYS) én verbod op de oude dubbele-rol-identifiers; node --check en unieke-ID-check (269, precies de vijf nieuwe ids bovenop 264). Browser-smoke-script mee-verhoogd: `browser-smoke-v7_5.mjs`.

## UI-mapping (ontwerpkeuze, gedocumenteerd)

De drie toestandsvelden zijn volledig onafhankelijk; de UI bindt ze bewust als volgt om fysisch identieke duplicaatstanden (lab+'none' ≡ corot+'none' ≡ corot+'wall') niet als schijnkeuzes aan te bieden:
- **frameSeg / verborgen checkbox** → uitsluitend `P.displayFrame`. Dit is het acceptatiecriterium: de toggle raakt geen enkel fysica-predicaat en verandert dus per constructie niets aan de ModelLog-diag-reeks (het diag-record bevat alleen solver-grootheden).
- **"Achtergrond Ω koppelen"** → aan = (`solverFrame='lab'`, `bgFlow='wall'`); uit = (`solverFrame='corot'`, wall→none). De oude wederzijdse-exclusiviteitsguard met het displayframe is vervallen: lab-solver + corot-display is nu een geldige, bereikbare stand — precies de stand voor de handmatige diag-vergelijking.
- **bundelveldkoppeling** → `bgFlow='bundle'`/'none'; overschrijft 'wall' met melding (enum-exclusiviteit).

## Observatie buiten scope (beslispunt voor v7.5.x)

Het checkboxlabel zegt "koppel coarse-grained bundelveld aan filamenten/**tracers**", maar `stepTracers` en `fieldVelocityAt` (stroomlijnen) sommeren het bundelveld niet — alleen `velocityCore` (filamenten) doet dat. Dit is bestaand v7.4.2-gedrag en is conform de spec ("geen wijziging aan … behalve waar frames expliciet genoemd") ongemoeid gelaten. Beslispunt: label aanpassen óf tracers/stroomlijnen het bundelveld geven.

## Validatie

- `validate-v7_5.py`: **PASS** (269 unieke IDs, node --check groen, alle markers, verboden identifiers 0×).
- Node-fysica-regressie (`extract_core.py` + `regression.cjs`, veldnaam-agnostisch en groen op zowel de d34-basis als deze build): T1 (3 kernen), T1b-sweep, T5-orde, T6-wrijvingsidentiteiten, B1-modusscheiding, B3-ghost-ontkoppeling, wandadvectie exact Ω×r uitsluitend bij lab+'wall', T9a-flux, bundelpredicaat, **T8 E_frame=6.6·10⁻⁸** — alles groen.
- **Verplicht aan jouw kant (kan hier niet):** `browser-smoke-v7_5.mjs` (≥10 frames zonder console-errors, `?selftest=1` volledig groen incl. T0i/T1b/T8, nieuwe HUD-rijen, frame-toggle-solverinvariantie, ε_rev-meting) én de handmatige spec-check: ModelLog aan, zelfde run in beide displayframes, identieke diag-reeksen.
- Verwacht zichtbaar gedragsverschil t.o.v. v7.4.2: geen — de refactor is gedragsbehoudend voor alle voorheen bereikbare standen; nieuw bereikbaar is alleen lab-solver + corot-display.

## Openstaand (plan v7 ongewijzigd)

Workbench-hernoeming WB-0.1 + pariteitsgate (D1/D2, parallel toegestaan) · v7.5.1 lift-falsificatie op de bundel (falsificatiecriteria vóór de eerste run) · v7.5.2–5 per ontwerpdoc · v7.6-S Rosetta + radiusDrive + T7.
