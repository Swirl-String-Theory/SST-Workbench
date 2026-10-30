# Gate2 Ruban Familywise Coupled Falsifier v0.2.1

**Status: DEVELOPMENT / `G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM`.**

Eén falsifier, vier achtereenvolgende gates, met keuze van knoopembedding, topologische knoopsoort, afzonderlijke torus-links, geometrieparameters en numerieke resoluties. **De geselecteerde seed wordt binnen deze falsifier opnieuw analytisch gegenereerd op hogere resolutie.** Je hoeft daarom **niet** steeds terug te gaan naar de E010-generator of duizenden XYZ-bestanden te importeren.

Dit project gebruikt de **ongewijzigde analytische formules en familieconfiguratie uit E010 v0.3.6**, die onder `src/vendor/` en `configs/` zijn opgenomen. Niet de Ruban-artikelen, niet KnotPlot en niet de oorspronkelijke 10.164 XYZ-bestanden zijn softwarematige runtimevereisten.

## Installatie (Windows 10/11, Python 3.10+)

Open een opdrachtprompt in deze versie-directory. Een virtuele omgeving is aangeraden:

```bat
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
run_all.cmd --list-families
```

De opdracht `run_all.cmd` voert eerst de regressietests uit en geeft eventuele extra argumenten ongewijzigd door aan `python -m src.pipeline`. `run_all.cmd` zonder argumenten draait de **pilot voor `T_2_3`**, inclusief de vier gates en één Euler-achtergrondproef. Het bestand `run_all.sh` doet hetzelfde onder Linux/macOS.

## Aanbevolen wetenschappelijke volgorde

Gebruik **een nieuwe `--run-id` per run**. De resultaten worden nooit stilzwijgend overschreven. De onderstaande volgorde is ontworpen om slechte kandidaten eerst goedkoop uit te sluiten en pas later veel rekentijd te besteden.

### Stap 0 — Alleen de keuzes bekijken

```bat
run_all.cmd --list-families
run_all.cmd --family T_2_3 --profile pilot --dry-run
run_all.cmd --topology 3_1 --profile fine --dry-run
```

Er zijn 24 torusknoop-embeddings, 6 torus-linkfamilies en 4 externe driecomponentige Borromeaanse kandidaatfamilies met elk drie gescheiden componenten. `--topology 3_1` selecteert de geometrisch verschillende `T_2_3` én `T_3_2`. `T_2_9`, `T_2_11` enzovoort zijn gewone selecteerbare families.

### Stap 1 — Beide trefoil-embeddings, breed maar nog goedkoop

```bat
run_all.cmd --topology 3_1 --profile pilot --screen-points 128 --refine-points 128,256,512 --promote-points 2048 --euler off
```

Standaard pilot: 16 waarden `B0 = 0.02, 0.04, ..., 0.32` en vijf waarden `Lambda = 3.4, 4, 5, 6, 7` voor iedere embedding. G1, G2 en G3 worden volledig uitgevoerd; G4 wordt in het gatebestand gemarkeerd als `NOT_RUN_USER_DISABLED`.

### Stap 2 — De trefoil-zoekband fijner bemonsteren

```bat
run_all.cmd --topology 3_1 --profile fine --screen-points 192 --refine-points 256,512,1024 --promote-points 2048,4096 --euler off
```

Fine: 121 waarden `B0 = 0.02` t/m `0.32`, stap `0.0025`. De falsifier genereert de winnaar na G3 **zelf opnieuw** bij zowel 2048 als 4096 punten, voor origineel én verstoord. Deze hoge-resolutiecoördinaten worden met individuele SHA-256-hashes geëxporteerd. Let op: het puntental van een **geometrie-export** is niet automatisch dat van de dynamische filamenttest.

**Noodzakelijke resolutiecontrole vóór een echte selectie.** De standaard G2-pilot op 128 punten is bewust goedkoop maar kan de kern bij hoge `Lambda` sterk onderresolven. Gebruik bijvoorbeeld deze gerichte controle op 1024 *dynamische* filamentpunten bij de bredere kern `Lambda=3.4`:

```bat
run_all.cmd --family T_2_3 --b0 0.16,0.20 --lambda-values 3.4 --screen-points 1024 --screen-steps 8 --final-time 0.003 --refine-points 512,1024 --promote-points 2048,4096 --euler off
```

Bij de uitgevoerde ontwikkelrun voldeden beide kandidaten aan de **ruimtelijke screeningheuristiek**, maar temporele convergentie en een volledige Euler-stationaire oplossing blijven ongetest. Dit is geen certificaat.

### Stap 3 — Overige torusknopen en nieuwe kandidaten

```bat
run_all.cmd --family T_2_5,T_2_7,T_2_9,T_2_11 --profile pilot --euler off
run_all.cmd --family T_3_4,T_4_3,T_3_5 --profile pilot --euler off
run_all.cmd --family T_2_9 --profile fine --promote-points 2048,4096 --euler off
```

Vergelijk **per embedding** de voorlopige optimale `(B0, Lambda)` in `G3_FAMILY_WINNERS.csv`. Verschillende torus-embeddings van dezelfde knoopsoort worden niet samengevoegd. Een winnaar op de rand van het gescande interval krijgt `B_at_scanned_edge=true`, geen automatisch fysisch optimum.

### Stap 4 — Driecomponentige torus-links (eerst beperkt)

```bat
run_all.cmd --family T_3_3 --b0 0.12,0.16,0.20 --lambda-values 3.4,4.0 --screen-points 96 --euler off
run_all.cmd --kind links --profile pilot --screen-points 96 --euler off
```

De generator maakt voor `T_3_3`, `T_3_6`, `T_3_9`, `T_6_9`, `T_6_15`, `T_6_21` afzonderlijke gesloten componenten. Niet één driemaal doorlopen knoop. De VortexLab-status `stalled-not-converged` uit KnotPlot wordt niet gepromoveerd tot nieuw Euler-resultaat.

### Stap 5 — Pas daarna de volledig gekoppelde Euler-pilot

```bat
run_all.cmd --topology 3_1 --b0 0.14,0.16,0.18,0.20 --lambda-values 3.4,4.0,5.0 --screen-points 192 --refine-points 256,512,1024 --promote-points 2048,4096 --euler preview --background single --max-g4 2 --euler-grid 48 --euler-holdout 64 --euler-curve-points 1024
```

Dit test de twee embeddingwinnaars met **één levende achtergrondlus**. `--euler-grid`/`--euler-holdout` slaan op het volledige 3D-Fourierrooster, niet op het aantal knooppunten van de centrumlijn. Een G4-test met spectrale filtering boven 10% krijgt `BLOCKED_SPECTRAL_UNDERRESOLUTION`; verhoog daarna de veldresolutie en controleer domein- en tijdconvergentie.

### Stap 6 — Daarna pas de configuratie met drie achtergrondkernen

```bat
run_all.cmd --family T_2_3 --b0 0.16,0.18,0.20 --lambda-values 4,5 --euler preview --background single,triple --euler-grid 48 --euler-holdout 64 --euler-curve-points 1024
```

### Stap 7 — Grote roosters: uitsluitend geometrische ontwikkelproeven

```bat
run_all.cmd --family T_2_3 --b0 0.16,0.20 --lambda-values 4 --euler preview --background 3x3,5x5 --euler-grid 32 --euler-holdout 48
```

**Niet kwalificeren als fysisch evenwicht** zolang de retourlussen elkaar naderen of kruisen. De huidige racetrack-constructie heeft reeds aantoonbaar te kleine afstanden gegeven. De geometrische preflight blokkeert daarom gevallen zonder voldoende positieve buisafstand.

### Stap 8 — Eén brede inventaris (optioneel, rekenintensief)

```bat
run_all.cmd --family all --profile pilot --screen-points 128 --euler off
run_all.cmd --family all --profile fine --screen-points 192 --refine-points 256,512,1024 --promote-points 2048,4096 --euler off
```

Met 30 analytische torusfamilies, 121 `B0`-waarden en vijf `Lambda`-waarden produceert de fijne G2-scan **18.150 gepaarde scenario's**, dus **36.300 nominale/verstoorde filamentruns**. Dat is niet hetzelfde als de 54.450 nog niet uitgevoerde E010-v0.3.6-scenario's die ook drie `delta_over_R0`-waarden registreren. Het `delta_over_R0`-scenarioattribuut is **niet** stilzwijgend meegenomen als dynamische variabele: er bestaat momenteel geen gekwalificeerde numerieke betekenis ervan in de G2-inductieoperator.

## Argumenten van `run_all.cmd`

| Argument | Betekenis | Standaard |
|---|---|---|
| `--family T_2_3` | Eén embedding; komma's voor meer; `all` voor 30 | `T_2_3` |
| `--topology 3_1` | Alle embeddings van één topologisch label | uit |
| `--kind knots` / `links` | Alleen één familieklasse | uit |
| `--profile pilot` / `fine` | 16 of 121 B0-varianten | `pilot` |
| `--b0 0.16,0.20` | Expliciete B0-subselectie | profiel |
| `--b-min 0.15 --b-max 0.21 --b-step 0.0025` | Eigen B0-grid | uit |
| `--lambda-values 3.4,4,5,6,7` | Volledige gezamenlijke B0/Lambda selectie | vijf waarden |
| `--seed-points 1024` | Analytische basisseedpunten per component | 1024 |
| `--screen-points 128` | Reductie naar filamentpunten tijdens snelle dynamica | 128 |
| `--screen-steps 3 --final-time 0.015` | Heun-stappen bij vaste dimensieloze eindtijd | 3 en 0.015 |
| `--max-segment-over-core 2` | Heuristische maximale segment/kernbreedte-ratio voor selectie; geen echte convergentiebewijs | 2 |
| `--refine-points 128,256,512` | Onafhankelijke G3-sampling voor winnaar | drie resoluties |
| `--promote-points 2048,4096` | Interne generatie van nieuwe hoge-resolutieseeds, mét hashes | 2048 |
| `--euler off` / `preview` | G4 overslaan of pilot uitvoeren | `preview` |
| `--background none,single,triple,3x3,5x5` | Achtergrondtopologie; comma-combinaties | single |
| `--max-g4 2` | Aantal geselecteerde kandidaten naar de zware G4-gate | 1 |
| `--euler-grid 48 --euler-holdout 64` | 3D Euler-rooster; U bevroren in holdout | 20 en 24 |
| `--euler-curve-points 1024` | Centrumlijnpunten voor gekoppeld Euler-veld | 1024 |
| `--euler-sigma 0.12 --euler-box 6` | Gaussian-kernbreedte en periodieke kubus | 0.12 en 6 |
| `--gamma-background 0.05` | Circulatie per achtergrondkern, t.o.v. totale knoopcirculatie 1 | 0.05 |
| `--run-id TEST_A` | Eigen unieke resultatenidentiteit; bestaande run-id geweigerd | tijdstempel + hash |
| `--dry-run` | Alleen geplande aantallen tonen | uit |

De argumenten `--family`, `--topology` en `--kind` zijn alternatieve selectiemethoden. Gebruik er één per run.

## Wat doet de falsifier precies?

**G1 — Geometrie.** Bouwt analytisch de 1 of 3 componenten op 1024 punten, meet randlengten, krommingsproxy's en sampled componentafstand. Geen exact reach-bewijs. De oorspronkelijke en verstoorde geometrieën worden uit de ongewijzigde E010-formule gemaakt.

**G2 — Dynamische screening.** Voor ieder `(embedding,B0,Lambda)` draait een nominale en een globaal volumebehoudend verstoorde seed een gereduceerd, geregulariseerd midpoint-filamentmodel gedurende dezelfde dimensieloze eindtijd. De score bevat het initiële rigide-residu, de na werkelijk integreren gemeten vormdrift en een kleine perturbatiegroeiterm. De **kernresolutiepreflight** slaat `segment_over_xi` en `dt_over_xi2` op; onderopgeloste kandidaten worden niet als gekwalificeerd aangemerkt. Als geen enkele seed de ruimtelijke heuristiek haalt, wordt nog wel een expliciet **ongekwalificeerde diagnostische** winnaar geëxporteerd. Het is nog steeds **geen** volledige driedimensionale Euler-simulatie of stabiele-eigenmodebewijs.

**G3 — Selectie, verfijning en interne seedpromotie.** Selecteert **gezamenlijk** de beste `B0` **én** `Lambda` per embedding. Vergelijkt de score op meerdere filamentdiscretisaties zonder hergebruik van oorspronkelijke E010-XYZ-bestanden. De hoog-resolutie geometrieën worden vervolgens on-demand, direct na de selectie, uit dezelfde parametrische formule gegenereerd en opgeslagen als `promoted_seeds/nominal/` en `promoted_seeds/perturbed/` met `G3_PROMOTED_FILES.json`. Een opgeslagen seed met 4096 punten is geen 4096-punts dynamisch bewijs.

**G4 — Euler-backreaction (ontwikkelmodel).** Maakt een periodiek Gaussian-mollified vorticiteitsveld van de gekozen knoop of link en één of meer volledig levende achtergrondlussen. Iedere vorticiteitscomponent krijgt dezelfde totale snelheid en een apart Euler-vorticiteitsresidu. Zoekt de gemeenschappelijke **axiale translatiesnelheid** `U_z` en test die bij een tweede rooster zonder opnieuw te fitten. De periodieke kubus heeft géén exacte continue rotatiesymmetrie, dus `Omega_z` wordt niet fit. Dit is een **voorwaartse Euler-pilot en residudiagnostiek**, nog **geen Newton–Krylov-volledige-veld-evenwichtszoeker**. Geen certificering van materieel topologiebehoud bij rooster-tijdintegratie.

## Output en reproduceerbaarheid

Iedere run krijgt een unieke map:

```
Gate2_Ruban_Familywise_Coupled_Falsifier_v0.2.1-outputs/
  runs/<run-id>/
    RUN_CONFIG.json
    G1_GEOMETRY.csv, G1_GATE.json
    G2_FILAMENT_SCAN.csv, G2_GATE.json
    G3_FAMILY_WINNERS.csv, G3_HOLDOUT.json
    G3_PROMOTED_FILES.json, G3_GATE.json
    promoted_seeds/{nominal,perturbed}/T_*_N2048.xyz
    G4_COUPLED.csv, G4_COUPLED.json, G4_GATE.json
    G0_G4_ASSESSMENT.json
    FALSIFIER_REPORT.md, FALSIFIER_REPORT.pdf
    MANIFEST_SHA256.json
  runs/<run-id>_outputs.zip
  runs/<run-id>_outputs.zip.sha256
```

De source-release heeft eveneens een eigen ZIP en SHA-256. Alle outputs hebben machineleesbare gates, instellingen, exacte bronhashes en een reproduceerbaar run-id. Geen bestaande run wordt overschreven. De scripts verrichten geen mutaties aan de E010-catalogus.

## Harde wetenschappelijke begrenzing

- De analytische torus-formule is geen geïmporteerde onafhankelijke KnotPlot-geometrie. KnotPlot-labels van links zijn metadata.
- De G2-filamentmodelvelden zijn géén exacte finite-core-Euler-oplossing. Er is geen aantoonbare convergentie naar een fysisch nulpunt.
- De Gaussian-kernen zijn niet compact ondersteund; de Fourier-filtering kan een groot deel van het veld veranderen.
- Een nul in de spectrale divergentie is onvoldoende voor materieel behoud van circulatie en topologie.
- Een gesamplede scheidingsafstand is géén rigoureuze continue bereik-/isotopiecertificering.
- De G4-holdout gebruikt dezelfde operatorimplementatie, dus is geen onafhankelijke backendpariteit.
- E010 registreert `delta_over_R0`, maar de huidige dynamische screen heeft daarvoor geen fysisch/numeriek geïdentificeerde rol; geen schijndekking.
- **Alle uitvoer behoudt wetenschappelijke eindstatus `G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM` totdat een niet-triviale, convergerende stationaire Euler-oplossing onafhankelijk is aangetoond.**


## v0.2.1 — eigen Borromeaanse kandidaten (geïmporteerde bestanden)

De vier nieuwe `BORRO_*`-families zijn **geen** analytische torusknopen en gebruiken
**geen** `B0`. Hun bron-XYZ/TXT en, indien aanwezig, JSON-metadata zijn integraal
meegeleverd in `data/external_borromean/` en voorzien van SHA-256-provenance.

| Selectie | Oorspronkelijke bestanden | Componenten | Status bron |
|---|---|---|---|
| `BORRO_FLAT` | `borromean_flat(1).txt` | 38 / 34 / 33 | Milnor onbewezen |
| `BORRO_BALANCED` | `borromean_balanced(1).txt` | 38 / 34 / 33 | Milnor onbewezen |
| `BORRO_5_5_6_TIGHT` | `LINK_5_5_6_TIGHT_N2048_ORIG_CPFIXED61.xyz` plus N1024 referentie | 2275 / 2109 / 2048 | STATIC_CANDIDATE |
| `BORRO_6_6_5_SOFT` | `LINK_6_6_5_SOFT_N2048_ORIG_CPFIXED61.xyz` plus N1024 referentie | 2229 / 2067 / 2048 | SHARP_TURN_WARNING |

De samenstelling van de gemengde links is volgens de aangeleverde metadata
`5_2,5_2,6_1` en `6_1,6_1,5_2`. Deze componentlabels zijn overgenomen als
bronmetadata; de **volledige link-isotopie** en Milnor's `mu_123` zijn `UNRESOLVED`.
Paargewijze nul-linking is noodzakelijk maar **niet voldoende** voor Borromeaanse isotopie.
`SHARP_TURN_WARNING` is een voorbehoud, geen PASS.

### Uitvoervolgorde voor deze eigen kandidaten

1. **Inventaris en dry-run** (geen simulatie):

```bat
run_all.cmd --list-families
run_all.cmd --topology BORROMEAN_UNCERTIFIED --lambda-values 3.4 --dry-run
```

2. **Eerst beide eenvoudige 3-componentvarianten:**

```bat
run_all.cmd --family BORRO_FLAT,BORRO_BALANCED --lambda-values 3.4,4.0 --seed-points 128 --screen-points 128 --screen-steps 8 --final-time 0.003 --refine-points 128,256 --promote-points 512,1024 --circulation-mode total --euler off --run-id BORRO_SIMPLE_PILOT
```

3. **Gemengde geknoopte componenten afzonderlijk:**

```bat
run_all.cmd --family BORRO_5_5_6_TIGHT --lambda-values 3.4 --screen-points 256 --screen-steps 8 --final-time 0.003 --refine-points 256,512 --promote-points 1024,2048 --euler off --run-id BORRO_556_PILOT
run_all.cmd --family BORRO_6_6_5_SOFT --lambda-values 3.4 --screen-points 256 --screen-steps 8 --final-time 0.003 --refine-points 256,512 --promote-points 1024,2048 --euler off --run-id BORRO_665_PILOT
```

4. **Controle van circulatienormalisatie** (zelfde geometrieën; andere
fysische hypothese):

```bat
run_all.cmd --family BORRO_FLAT,BORRO_BALANCED --lambda-values 3.4 --screen-points 128 --refine-points 128,256 --promote-points 512 --circulation-mode per-component --euler off --run-id BORRO_PER_COMPONENT
```

5. **Pas na geometrie-/tijd-/ruimtelijke convergentie:** gekoppelde Euler-
**ontwikkeltest**, niet evenwichtscertificatie:

```bat
run_all.cmd --family BORRO_BALANCED --lambda-values 3.4 --screen-points 256 --refine-points 128,256 --promote-points 1024 --euler preview --background single --max-g4 1 --euler-grid 48 --euler-holdout 64 --run-id BORRO_EULER_PREVIEW
```

Bij externe seeds doet `--promote-points` **periodieke booglengte-interpolatie**
van het originele gesloten veelhoekmodel (alle componenten onafhankelijk).
Het kan géén ontbrekende hoge-frequentiedetails uit bronbestanden herstellen.
Deze interpolatie is **geen analytische nieuwe embedding** en **geen bewijs dat
isotopie of knoopdikte behouden blijft**. Een eenvoudige invoerseed van 38 punten
blijft bijvoorbeeld 38 oorspronkelijke meetpunten hebben, ook na export op 4096.

**Belangrijk over B0:** `--b0`, `--b-min` en `--b-max` zijn niet betekenisvol
voor deze geïmporteerde families en worden bij gelijktijdige selectie geweigerd.
`--family all` bevat nu **34 families** (30 analytisch + 4 geïmporteerd) en
`--kind links` bevat **10** linkfamilies.

`--circulation-mode total` (standaard): elk van drie componenten heeft
`Gamma=1/3`, zodat de som van de ondertekende componentcirculaties 1 is.
`--circulation-mode per-component`: elke component krijgt `Gamma=1`.
Scores van deze protocollen mogen niet ongecorrigeerd als gelijke
fysische levensduur of gekoppelde energiewaarde worden vergeleken.

**Hardste wetenschappelijke beperking:** met `mu_123=UNRESOLVED` mogen deze
geometrieën niet als bewezen Borromeaanse topologie, niet als stabiel gekoppeld
systeem en niet als fysisch Euler-evenwicht worden geclassificeerd.


### Variabele bronresolutie: 1024 tegenover 2048

De twee samengestelde links zijn elk in twee onafhankelijke bron-discretisaties
meegeleverd. Het werkelijke aantal vertices per component is niet overal 1024
of 2048 (zie tabel boven). Voor een **directe N1024-broncontrole** gebruik:

```bat
run_all.cmd --family BORRO_5_5_6_TIGHT --external-source reference --lambda-values 3.4 --seed-points 1024 --screen-points 256 --refine-points 256,512 --promote-points 1024 --euler off --run-id BORRO_556_SOURCE1024
run_all.cmd --family BORRO_5_5_6_TIGHT --external-source original --lambda-values 3.4 --seed-points 2048 --screen-points 256 --refine-points 256,512 --promote-points 1024 --euler off --run-id BORRO_556_SOURCE2048
```

Herhaal voor `BORRO_6_6_5_SOFT`. `--external-source reference` is niet geldig
voor FLAT of BALANCED omdat daarvoor slechts één bronresolutie bestaat.
Door gelijke `--screen-points`, `--final-time`, `--screen-steps` en `--lambda-values`
te hanteren isoleren deze runs het verschil van de bron-discretisatie.

Gemakselecties: `--kind borromean` = vier geïmporteerde families;
`--kind torus-links` = zes analytische torus-linkfamilies;
`--kind links` = alle tien driecomponentige linkfamilies.


### Import-auditbestand

Elke run met `BORRO_*` schrijft bovendien `G1_IMPORTED_LINK_PROVENANCE.json`:
originele bronhashes, werkelijke puntenaantallen per component, gedeclareerde
componentknopen, bronwaarschuwingen, **benaderde** Gauss-linkinggetallen en voor
de twee bronresoluties hun gesamplede bidirectionele afstand.
Dit is geen bewijs van de Milnor-invariant of van volledige link-isotopie.
De oorspronkelijke bestanden worden nooit gewijzigd of door de nieuwe
interpolatiebestanden vervangen.
