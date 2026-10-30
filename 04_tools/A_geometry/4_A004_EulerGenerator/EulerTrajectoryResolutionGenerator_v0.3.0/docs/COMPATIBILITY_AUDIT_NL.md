# Compatibiliteitsaudit — Euler Trajectory Resolution Generator v0.2.0

**Bronnen:** lokaal geverifieerde gepinde A075-v0.2.9/v0.2.10 en A077-v0.1.2 Pythonkernels, originele A026-exportpatch; aanvullende recente Drive-documentatie A064-v0.2.0, A068-v0.4.4, A060-v0.3.0 README en onderzoeksoverzicht uit recente SST-conversaties. De actuele bronnen van alle overige projectfamilies zijn niet lokaal hash-gecontroleerd; toepasselijkheid is een _adapterkandidaat_, geen bevestigde integratie.

## Vier onderscheiden gegevensvarianten

| Variant | Inhoud | Producer / vereiste | Wetenschappelijke betekenis |
|---|---|---|---|
| **V1 Volumetric Euler + passieve trajecten** | tijd, 3D punttrajecten, veldsnelheid, energie/heliciteit/divergentie, grid/core/box | Echt geëvolueerd 3D Euler-veld met samengevoegde RK4-stadia | Vloeistofdeeltjes, geen wervelkern of spin |
| **V2 Materiële oppervlakte en kelvinlus** | materiële mesh/coördinaten, normale vector, rek, volume, ω·n, Γ_lus | Solver die **dezelfde RK4-veldsubstadia** en materiaaloppervlakken transporteert | Kandidaat vortexbuis alleen na tangentie/volume/topologie/kringintegraaltests |
| **V3 Filament/curve ensemble** | polylijn per tijd, kernradius, circulatie, framings/twist, remeshing + zelfintersectie | Eindige-kern/filament/Biot–Savart- of geometrische provider met eigen dynamica | Niet uitwisselbaar met Euler-veldtrajecten; geen 3D Euler-G8 |
| **V4 Observatie-/fase- en memory-transport** | afgeleide q(t), qdot(t), fase, observatieoperator, onafhankelijke trial-id | Verifieerbare V1/V2/V3-dynamica + onafhankelijke analyse | Geen nieuwe fysische provider, alleen analyse/export; geen pseudo-replicatie |

## Kandidaten en prioritering

| Familie | Bestaande methode volgens beschikbare bron | Passende variant | Integratiestatus en noodzakelijke adapter |
|---|---|---|---|
| **A075** | Periodiek 3D Euler-veld, Ruban/gekoppelde bron, eerdere A026-exporter | **V1** | **Uitvoerbaar en getest** voor dezelfde `euler3d.py` in v0.2.9/v0.2.10; v0.2.14-NK is een aparte geometrische addon, niet automatisch dezelfde dynamische provider |
| **A077** | Periodiek 3D Euler-pilot met toroïdale/meridionale beginvelden en gereduceerde ring-ODE | **V1**, later **V2** | **Uitvoerbaar en getest** voor v0.1.2 `euler_field.py`; laat V3-ringproxy niet meetellen als V1-Euler |
| **A026 Hidden State Memory** | Geschiedenis-vs-huidige toestand; donor-export is A075 | **V4** uit V1 | Maak formaatadapter (`q_m`, `qdot_m_s`, trial-ID). Onafhankelijke veldrealisaties en getrainde/heldout-splits vereist, niet markers/tijdsamples als replicaten |
| **A068-v0.4.4** | Volledig Euler-veld én **reeds geïntegreerde Lagrangiaanse materiële torus**, vorticiteitstangentie, volledige-veld-terugkeer | **V2**, optioneel V1 | **Niet** vervangen door punttracers. Bestaande A068-surface-indexering, normale, volume, full-field-symmetrie en RPO-evidence moeten als aanvullende gespecialiseerde data blijven bestaan. Oorspronkelijke A064-provider eerst hash-pinnen |
| **A064-v0.2.0** | Euler-veld, levelsets, onafhankelijke materiële tracerpassages over separatrices | **V1 + V2-transport** | Nieuwe adapter voor A064-veldvorm/snapshots; levelset is niet materieel, dus bewaar relatieve-normaalflux en onafhankelijke kandidaat/holdout |
| **A060** | Overkoepelende evidence-provenance/closurecoördinatie, geen eigen universele Euler-dynamica | **V4 intake** | Alleen bestaande onafhankelijk gekwalificeerde resultaten inlezen, geen nieuwe solverclaim; bron-ID en family provenance behouden |
| **A073** | Geschetste discrete, vervormbare achtergrondkernen vs een vrije trefoil | **V3**, later V2 | **Voorwaardelijk:** vereis gescheiden materiaal-kernen, ring- en achtergrondidentiteiten, wederzijdse terugkoppeling en linearisatie/perturbaties. Louter tracerpunten of gemiddeld roterend continuüm zijn onvoldoende |
| **A074** | Trefoil kracht/transport, wisselende filament- en veldbenchmarks | **V3** of **V1** afhankelijk van exacte producer | Alleen na concrete solverbroncheck; krachtschaal en onafhankelijke circulatiebron expliciet bewaren |
| **A054/A057** | Zelfherstel, variatiestabiliteit, geometrie versus Euler-energie | **V3** voor filament; **V1/V2** wanneer onafhankelijke Euler-velddynamica aanwezig | Geen statuspromotie op alleen geometrierelaxatie of FK/filament-Hamiltoniaan |
| **A031/A038/A051/A056** | Kelvin, RPO/Floquet, fasesynchronisatie en modaliteit | **V4** afgeleid uit V1/V2 | Alleen echte, gekwalificeerde tijdvelden en faseobservabelen; RPO/klok-eisen apart; hergebruik is afhankelijk van nog open eigen gates |
| **A063 (Hill/Hicks)** | Analytische Euler/Beltrami/separatrix benchmark | **V1 referentie** | Geschikt als analytische/structurele regressie, niet als externe onafhankelijke Euler-dynamica; vereist expliciete veldevaluator |
| **A045/A046/A048/A060**, afhankelijk van concrete input | Topologie, triadische vorticiteit, druk/energie- en veldclosure | **V1 veldsnapshot** of V4 | Alleen na per-project broncontrole en evaluatie van observabele; actuele naam- en catalogusconflicten mogen niet worden geraden |
| **E010/E011/E013** | Knoopgeometrie/seed- of carrierproviders | **input voor V3/V2/V1-initialisatie** | Statische seed is geen tijdafhankelijke Euler-trajectdataset en geen onafhankelijke dynamica-provider |

## Wetenschappelijke interfacecontracten

- **V1**: `time_abs`, `x_unwrapped`, `u(x,t)`, `domain`, `n`, `dt`, `core_model`, `source_hash`, `equation_provider`, `run_group_id`.
- **V2**: V1 plus `material_surface_vertices(t)`, `faces`, `closed_oriented`, `normal`, `integral_omega_dot_n` op specifieke open doorsnedes, `circulation_loop`, `volume_error`, `topology_status`.
- **V3**: `filament_id`, `X_i(s,t)`, `gamma_i`, `a_i`, `framing/twist`, `remeshing`, `minimum_interfilament_gap`, `geometry_hash`; **niet** de V1 `u(x,t)` toekennen zonder onafhankelijke veldberekening.
- **V4**: `observable_definition`, `q(t)`, `dqdt`, `conditioning_history`, `initialization_family`, `holdout_family`, `trial_id`, `split_provenance`; geen V1/G8-PASS uit V4-only data.

### Belangrijke bronverwijzingen in de audit

- A068 v0.4.4 rapport: https://drive.google.com/file/d/1SIeG2toWX9aPgawfm-AJhfI2U1AKQTxF/view
- A064 v0.2.0 rapport: https://drive.google.com/file/d/1MQflWR-Gb-903BEO3u0ICY6AiOpmYej8/view
- A060 v0.3.0 README: https://drive.google.com/file/d/1l7bBpWJ_QDHRkZJzHk4YTe1XEProOEhp/view

**Besluit:** twee V1-adapters zijn operationeel. V2 (materiaaloppervlakken), V3 (filamenten) en V4 (afgeleide observabelen) zijn **gespecificeerde uitbreidingscontracten, geen reeds geïmplementeerde, gevalideerde adapters**. De bestaande frozen releases blijven ongewijzigd.
