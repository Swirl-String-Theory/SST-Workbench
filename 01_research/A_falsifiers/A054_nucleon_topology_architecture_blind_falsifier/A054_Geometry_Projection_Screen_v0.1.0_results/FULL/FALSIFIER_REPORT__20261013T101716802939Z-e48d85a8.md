# A054 Geometry Projection Screen v0.1.0 - FULL result

**Datum:** 12 oktober 2026. **Status:** NUMERICAL SCREENING, NO A054 ADMISSION, NO A057 TRANSFER.

## Uitgevoerde dataset

- 50/50 bestaande KnotPlot-censusgeometrieën gelezen (20 knots, 16 links/unlinks, 14 torusconfiguraties).
- 2 geometrische armen per bron: `native` en `uniform300_no_relax` (deterministische polygonale booglengte-interpolatie, geen `ago`).
- S0/S1/S2 numeriek uitgevoerd op alle 100 armen, met 2 Bishop-Fourier-modi per component en A054-analyseresolutie circa 96 beads.
- 100/100 armen: herhaalde projectie P(P(X)) verandert geometrie >1e-10 (relatieve RMS-diagnose, geen fysische gate).
- 2/100 Hessiaanproeven voldoen aan de vaste numerieke convergentievoorwaarde 0.25 inclusief sign class; 98/100 niet.
- De 2 geslaagde Hessiaanproeven behoren **beide tot 8_17** (native en uniform300_no_relax), maar hun stationariteit sigma is respectievelijk 1.688122 en 1.690914. De geregistreerde stationariteitsdrempel is sigma <= 0.1. Dus nul geadmitteerde SST-toestanden.
- 5 historische E013-providerseeds en 2 KnotPlot `ago`-exports zijn in een separaat referentiepanel numeriek vergeleken (zie REFERENCE_OVERLAYS.jsonl); ook dit zijn geen onafhankelijke bevestigingsproviders.

## Geometriesamenstelling

| Corpus | Aantal |
|---|---:|
| KnotPlot knot-labels | 20 |
| KnotPlot link- en unlink-labels | 16 |
| KnotPlot torus T(p,q) | 14 |

## Mediaanvergelijking

| Metriek | Native | Uniform300 zonder relaxatie |
|---|---:|---:|
| Bead-afstand-CV | 0.026325 | 0.005492 |
| Relatieve projectie-energiedrift | 0.000354789 | 0.000327963 |
| Hessian rel-Frobenius error | 0.498326 | 0.496986 |

**Interpretatie:** gelijkmatiger bead-afstand is inderdaad gerealiseerd, maar levert op dit corpus geen globale Hessiaanreparatie op. Sommige individuele resultaten verbeteren, andere verslechteren. De niet-gladde reach/projection branch is kandidaat voor verder onderzoek, **niet bewezen primaire oorzaak**.

## Dekking nog niet volledig

- Twistladder 3 t/m 10 crossings aanwezig. Twistknoop met 11 crossings niet geverifieerd of aangeleverd.
- De 18 Knot Atlas prime links met maximaal 7 crossings zijn als doelen opgenomen, maar KnotPlot-inventaris (11 relevante link labels 2-7 crossings; 2 unlink-controls en 3 hogere labels) is nog niet één-op-één via invarianten aan de Atlas gekoppeld.
- Geen originele KnotPlot `refine nbeads 300` zonder `ago` uitgevoerd. `uniform300_no_relax` is een transparant Python-alternatief, *niet exact KnotPlot-refine*.
- Geen volledige toestandselectie, dynamische ringdown of onafhankelijke providerreplicatie uitgevoerd.

## Reproduceerbaarheid

`run_all.cmd TEST`, `run_all.cmd` (BASIC), `run_all.cmd FULL` (100 Hessiaanvarianten), `run_all.cmd RESUME`.
Bronnen in `inputs/`, bronhashes in `SOURCE_FILES_SHA256.json`, geanalyseerde rijen in `results/FULL/ROWS.jsonl` en `SCREEN_RESULTS.csv`.
Het geauthenticeerde Google Drive-bronarchief `falsifier_census_v0.1.0_output.zip` is opgenomen met exacte SHA-256 `1719c90500a2ae240e150f5442d18b253377f9ef3ecc3fddfee361c19a54866b`. Het is niet hetzelfde archief als de eerdere `original_zip_sha256` uit `census_targets.json`; die twee hashes mogen niet worden verward.

## Frameworkkwalificatie

Numerieke thresholds (EPS=0.015, Hessian <=0.25, stationarity <=0.1) ontleend aan de frozen A054-configuratie; **framework-v1.0.7 runtime is niet ingebed en zijn 56 regressietests zijn niet opnieuw uitgevoerd.** De hier uitgevoerde 7 lokale unit/parity-tests zijn een ander niveau. Deze diagnostische run is geen officiële A054-v0.5.2 FULL/CERTIFY of BLIND-campagne.

## Bronverwijzingen

- KnotPlot census v0.1.0 (oorspronkelijke TXT/KPF, Google Drive SST-Workbench).
- A054 v0.5.1 `geometry.py`, `dynamics.py`, `energy.py`, `configs/basic.json` als rekencontract-referenties.
- Knot Atlas, *Link table - up to seven crossings* voor de lijst van 18 linkdoelen.
