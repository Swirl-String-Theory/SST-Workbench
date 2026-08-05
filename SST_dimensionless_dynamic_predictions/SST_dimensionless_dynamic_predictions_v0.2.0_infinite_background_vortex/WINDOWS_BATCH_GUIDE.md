# Windows batch-handleiding

## Doel

Deze scripts voeren het SST-pakket stapsgewijs uit zonder dat je handmatig lange Python-commando's hoeft te typen.

De scripts gebruiken een lokale virtuele omgeving:

```text
.venv\
```

Daardoor worden de Python-pakketten voor dit onderzoek geïsoleerd van andere Python-projecten.

## Voorbereiding

1. Pak de ZIP volledig uit, bijvoorbeeld naar:

   ```text
   C:\SST\SST_dimensionless_dynamic_predictions_v0.1.0_windows_batch\
   ```

2. Installeer Python 3.11 of nieuwer.
3. Dubbelklik achtereenvolgens op de genummerde bestanden in `batch\`.

Voer de scripts niet rechtstreeks vanuit een geopende ZIP uit. De hele map moet eerst zijn uitgepakt.

## Aanbevolen volgorde

### Stap 0 — Python controleren

```text
batch\00_check_python.bat
```

Toont de gevonden Python-versie, executable en Windows-platforminformatie.

### Stap 1 — Virtuele omgeving installeren

```text
batch\01_setup_venv.bat
```

Dit doet:

```bat
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install -e .
```

### Stap 2 — Interne sanity check

```text
batch\02_selftest.bat
```

De ring moet onder meer een kleine `projected_residual`, eindige energie en positieve sampled reach krijgen.

### Stap 3 — Snelle campagne

```text
batch\03_quick_campaign.bat
```

Test:

- ring `0_1`;
- trefoil `3_1`;
- spiegel-trefoil;
- figure-eight `4_1`;
- Rosenhead- en Winckelmans-kernels;
- één resolutie en één regularisatieschaal.

Uitvoer:

```text
outputs\quick_batch\campaign_results.json
outputs\quick_batch\campaign_summary.csv
outputs\quick_batch\convergence_summary.csv
```

### Stap 4 — Alle knopen statisch diagnosticeren

```text
batch\04_diagnose_all_knots.bat
```

Maakt per knoop een JSON-bestand met onder meer:

- lengte en RMS-radius;
- sampled reach;
- curvature-statistieken;
- energy proxy;
- impulse norm;
- rigid-motion fit;
- `relative_motion.projected_residual`.

Interpretatie van de residu-gate:

```text
projected_residual < 0.05   kandidaat relative equilibrium
projected_residual >= 0.05  statische invoervorm faalt deze gate
```

Dit is een numerieke research-gate, geen bewijs van een elementair deeltje.

### Stap 5 — Trefoil evolueren

```text
batch\05_evolve_trefoil.bat
```

Hier wordt de trefoil kort geëvolueerd met de Winckelmans-kernel. Let in het JSON-bestand vooral op:

- `final_recurrence_error`;
- `relative_energy_drift`;
- `dominant_shape_frequency`;
- de tijdreeks van vorm- en energiematen.

Een kleine statische residu is niet genoeg. Een dynamische deeltjeskandidaat vereist uiteindelijk een kleine recurrence error en een geconvergeerde Floquetanalyse.

### Stap 6 — Medium convergentiecampagne

```text
batch\06_medium_campaign.bat
```

Deze gebruikt:

```text
resolutions = 96, 128
epsilons    = 0.075, 0.10
kernels     = Rosenhead, Rankine, Winckelmans
```

Hiermee controleer je of dimensieloze ratio's stabiel blijven wanneer numerieke keuzes veranderen.

### Stap 7 — Volledige researchcampagne

```text
batch\07_full_research_campaign.bat
```

Deze gebruikt de volledige ladder:

```text
resolutions = 96, 128, 192, 256
epsilons    = 0.05, 0.075, 0.10, 0.125
kernels     = Rosenhead, Rankine, Winckelmans
steps       = 400
```

De run is alleen wetenschappelijk bruikbaar wanneer een ratio tegelijk convergeert onder:

1. hogere resolutie;
2. verschillende regularisatieschalen;
3. minstens twee admissibele kernels;
4. dezelfde normalisatie en circulatie.

### Resultaten openen

```text
batch\08_open_results.bat
```

### Gegenereerde resultaten verwijderen

```text
batch\09_clean_generated_outputs.bat
```

De meegeleverde validatie-output `outputs\quick_start` wordt daarbij niet verwijderd.

## Automatische pijplijnen

Installatie + selftest + quick campaign:

```text
batch\90_run_quick_pipeline.bat
```

Selftest + statische diagnose + evolutie + medium campaign:

```text
batch\91_run_analysis_pipeline.bat
```

## Welke resultaten zijn de feitelijke voorspelling?

Niet een absolute energie of snelheid, maar bij voorkeur een dimensieloze verhouding ten opzichte van de ring:

```text
energy_proxy_ratio
rigid_rate_ratio
deformation_rate_ratio
impulse_norm_ratio
dominant_shape_frequency_ratio
```

Een kandidaatvoorspelling moet:

- vooraf als observable gekozen zijn;
- geen `alpha`, `m_e`, `G`, `a_0` of andere targetconstante gebruiken;
- stabiel zijn onder resolutie, epsilon en kernel;
- uit een dynamisch gecertificeerde toestand komen;
- daarna pas extern worden vergeleken.

## Configuratie wijzigen

Kopieer bijvoorbeeld:

```text
configs\medium_campaign.json
```

naar:

```text
configs\my_campaign.json
```

Pas vervolgens `resolutions`, `epsilons`, `kernels`, `cases` en `evolution` aan. Gebruik daarna:

```bat
.venv\Scripts\python.exe src\sst_dimensionless_ratios.py campaign --config configs\my_campaign.json --output outputs\my_campaign
```

## Veelvoorkomende fouten

### `Python is niet gevonden`

Installeer Python 3.11+ en selecteer tijdens installatie `Add Python to PATH`.

### `No module named numpy`

Voer `batch\01_setup_venv.bat` opnieuw uit.

### `ideal knot not found`

Controleer dat `data\ideal_favorites.txt` aanwezig is en dat de volledige pakketmap is uitgepakt.

### Een campagne wordt onderbroken

De JSON/CSV-bestanden worden per voltooide run geschreven. Start dezelfde batch opnieuw; de vaste outputmap wordt bijgewerkt.

## Infinite background vortex (v0.2.0)

De nieuwe achtergrond is de limiet van een Rankine-vortex met oneindige radius:

\[
\mathbf u_{\rm bg}=\boldsymbol\Omega_{\rm bg}\times\mathbf r,
\qquad
\zeta_{\rm bg}=2\Omega_{\rm bg}.
\]

De SST-genormaliseerde waarde is:

\[
\zeta_{\rm bg}^*=\frac{1}{\pi}.
\]

### Snelle gepaarde test

```text
batch\10_infinite_background_vortex_quick.bat
```

Dit vergelijkt `zeta*=0` met `zeta*=1/pi` onder fixed-sampled-reach-normalisatie.

### Sterkteladder

```text
batch\11_infinite_background_vortex_ladder.bat
```

Deze test co- en counter-rotatie:

```text
{-2,-1,-0.5,0,0.5,1,2}/pi
```

### Korte trefoil-evolutie

```text
batch\12_infinite_background_vortex_evolution.bat
```

Deze vergelijkt de trefoil in het stilstaande medium met dezelfde trefoil in de
uniform roterende achtergrond.

### Automatische invariantie-audit

```text
batch\13_analyze_background_vortex_results.bat
```

De primaire gate gebruikt `relative_equilibrium_residual`, dat in v0.2.0
intrinsiek wordt genormaliseerd op de zelfgeïnduceerde vormsnelheid. Gebruik
`total_normalized_residual` niet als stabiliteitsgate: die kan kunstmatig dalen
wanneer alleen extra rigide achtergrondrotatie aan de noemer wordt toegevoegd.
