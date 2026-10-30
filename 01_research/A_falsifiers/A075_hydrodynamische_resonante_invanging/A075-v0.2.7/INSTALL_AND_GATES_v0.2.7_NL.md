# A075-v0.2.7 — Installatie & kwalificatie (Windows)

## Installatie

Pak de bron-ZIP onder `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\` uit. Het archief bevat `A075_hydrodynamische_resonante_invanging\A075-v0.2.7\` en overschrijft v0.2.6 niet. Gebruik je eigen werkende `C:\workspace\projects\SST-Workbench\.venv-a075-xpu` (PyTorch `2.12.1+xpu` werd eerder op de Intel Arc A770 gevalideerd). Als die XPU-omgeving niet wordt geactiveerd, mogen de GPU-gates niet slagen.

```bat
cd C:\workspace\projects\SST-Workbench
.venv-a075-xpu\Scripts\activate.bat
cd 01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.7
python -m pip install -r requirements.txt
python -m pytest -q tests
python tools\check_sources.py
python tools\preflight_contract.py
python tools\build_native.py
run_all.cmd GPU_PROBE
```

Na een volledig geslaagde preflight en uitsluitend voor deze nieuwe versie:

```bat
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --grid-up 112 --threads 12 --allow-expensive --heartbeat-seconds 10
```

Deze BASIC voert het wetenschappelijke Euler-scenario uit, de twee compacte operator-pariteitscontroles en de door Framework v1.1.0 verplichte 2-uit-3 werkelijk uitgevoerde backendmatrix. Hij doet standaard **geen** domeinladder. Een geslaagde CPU/GPU-probe alleen telt niet als een wetenschappelijke uitvoering.

## Optionele periodieke domeingevoeligheid

```bat
run_all.cmd BASIC --grid 80 --threads 12 --domain-study-only --domains 10:80,15:120,20:160 --knots 0_1 --allow-expensive --plan
run_all.cmd BASIC --grid 80 --threads 12 --domain-study-only --domains 10:80,15:120,20:160 --knots 0_1 --allow-expensive
```

De `domain-study-only`-run maakt een **afzonderlijke diagnostische map** met een unieke run-ID, zonder het frameworkprotocol of de officiële BLIND-archieven te veranderen. Dit is geen Framework-G10-PASS, en het is nadrukkelijk geen vrije-ruimte-oplosser.

Wil je de extra domeinladder **in dezelfde Framework-BASIC-run** opnemen, gebruik dan `--domain-study` (zonder `-only`). Dit rekent aanzienlijk langer: standaard Euler-verfijningen, optionele domeinladder, twee parity screens en automatische backendmatrix. G10 beoordeelt uitsluitend of de domeinladder bij vaste fysieke roosterafstand daadwerkelijk is uitgevoerd.

## Resultaten inspecteren

```bat
run_all.cmd STATUS
```

Inspecteer in de runoutput: `SOURCE_MANIFEST.json`, `science/SOURCE_QUALIFICATION.json`, `science/BACKEND_OPERATOR_PARITY.json`, `AUTO_BACKEND_MATRIX.json`, `GATE_LEDGER.json`, optioneel `science/domain_study/DOMAIN_MATRIX.json` en `SCIENCE_EVIDENCE_MANIFEST.json`.

**Stopcriteria:** gewijzigde of ontbrekende bronhash; onjuiste framework-runtime; ontbrekende native of GPU-implementatie voor de vereiste backendmatrix; numerieke divergentie; onopgeloste knoopidentiteit. Hardwarebeschikbaarheid, backenduitvoering en fysische gates worden afzonderlijk beoordeeld.

## Statussen

- **G1:** alleen byte-exacte bronresolutie, geen onafhankelijk experiment.
- **G5/G6:** operatorpariteit op twee vooraf gekozen kleine Euler-velden. Deze PASS-waarde is diagnostisch en bevestigt *niet* de volledige oplosserconvergentie.
- **G7:** vereist originele `KNOT_5_2_N2048_ORIG.xyz` en `KNOT_6_1_N2048_ORIG.xyz`, gevolgd door afzonderlijke topologische verificatie.
- **G10:** optionele periodieke beeldgevoeligheid; laat `G8` en de vrije-ruimte-beperking open.
- **G3/G8:** blijven UNRESOLVED totdat bronvertrek, eigen klok, minimaal honderd klokcycli, ruimtelijke/temporele/core/box-convergentie en lokale fluxsluiting objectief zijn bewezen.
