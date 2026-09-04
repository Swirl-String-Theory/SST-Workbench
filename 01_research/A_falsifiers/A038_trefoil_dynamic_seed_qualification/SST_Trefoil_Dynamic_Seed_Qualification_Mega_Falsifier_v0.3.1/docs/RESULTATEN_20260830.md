# SST v0.2.2 — atlas en Fase B: implementatie en echte run

## Uitkomst

Er zit genoeg in de repo om een gecontroleerde nieuwe poging te doen. Die poging
is nu geïmplementeerd en uitgevoerd in een **aparte v0.2.2**. De v0.2.1-code en
oude evidence zijn in deze beurt niet gewijzigd.

Er zijn zes nieuwe geometrieën uit **drie verschillende constructielijnen**
gemaakt. Dit is een prospectieve holdout van nieuwe realisaties, **niet** een
atlas van drie volledig ongeziene upstream-bronnen of drie statistisch
onafhankelijke fysieke datasets. De oorspronkelijke geometrieën waren al
beschikbaar; kleine vervormingen wissen die geschiedenis niet uit.

De echte run blijft numeriek geblokkeerd: **S37 0/4**, daarna geen S40–S60
trajecten en geen trefoil-Floquet- of interventiecertificaat. De uitkomst is
`INDETERMINATE`, niet een fysieke SST-falsificatie.

## Aangewezen atlas en bewijsstatus

Lokale atlas:

`C:\workspace\projects\SST-Workbench\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.2.2\artifacts\prospective_atlas_20260830\test_atlas`

| Constructielijn | Herkomst | Nieuwe testrealisaties | Status |
|---|---|---:|---|
| Fremlin Fourier | `Fremlin_FourierSeries/fremlin/3_1/knot.3_1.short` | 2 | Andere provenance dan Gilbert en braid; historisch bekende ouder |
| Gilbert/SONO Fourier | `Knot_Library/Sources/Ideal_Gilbert/extracted/3_1/3_1_AB.txt` | 2 | Afzonderlijke SONO/Fourier-constructielijn; geen claim dat de ouder ongezien was |
| SST braid closure | Knot Library v0.2.3, `braid_closure(2,[1,1,1])` | 2 | Zelfstandige constructiemethode; geen externe empirische dataset |

Gilberts database beschrijft SONO-relaxatie en Fourier-representaties van
benaderde ideale knopen; dit garandeert geen globaal minimum.
[Bronbeschrijving](https://katlas.org/wiki/Ideal_knots).

Alle zes realisaties hebben een numeriek gecontroleerd trefoil-diagram bij
N=64,96,128. De checker controleert de daadwerkelijke geprojecteerde polygonen,
niet alleen hun bestandsnaam of braid-label. De gevonden drie-crossing
Gaussstructuur correspondeert met de trefoil-presentatie in
[Knot Atlas](https://katlas.org/wiki/3_1). Dit blijft `SUPPORTED`: float64 met
marges, geen intervalbewijs of externe space-curve-certificatie. Handedness is
niet als apart gebalanceerde factor ontworpen; bronvergelijkingen zijn daarom
ook geen causale effecten van constructiefamilie.

### Preregistratie en reserve

- Vastgelegd vóór het genereren of dynamisch scoren van deze zes realisaties:
  code, bron/dependency-hashes, configuratie, Fase-B-protocol en seed-commitments.
- Registratietijd: `2026-08-30T13:11:43.390468+00:00`.
- Commitment: `1ab8082fa341ce61a0c7377a8c6b747ef56323166dac8fcbaaf4505fba049595`.
- Geometrische afkeuring leidt niet tot opnieuw trekken.
- Zes vooraf bepaalde testrealisaties; geen adaptieve S25-verfijning of extra
  kandidaatvarianten. De dynamische BASIC-drempels zijn niet verruimd.
- Reserve: aparte seed vastgelegd; **geometrieën niet gegenereerd en niet
  gescoord**. Reserve-seed blijft lokaal in `sealed/seeds.json`, buiten de
  opleveringsbundel.
- De testset is na deze run verbruikt als holdout. Ouders en huidige testresultaten
  kunnen voortaan ontwikkel-/regressiedata zijn, geen nieuwe blinde evidence.
- De scoring leest opaque IDs; bronidentiteiten worden apart bewaard en pas
  gereveald na de keten. Dit is pipeline-blinding, geen onafhankelijke menselijke
  datacustodian of toegangsbeveiliging via encryptie/ACL.
- Zowel de codefreeze als de reveal-commitments zijn na afloop geverifieerd.

## Werkelijke run

| Gate | Getest | Door | Betekenis |
|---|---:|---:|---|
| S10 | 6 | 6 | 3 gedeclareerde constructielijnen geaccepteerd |
| S20 | 6 | 6 gescoord | Screening, geen fysische bevestiging |
| S30 | 6 | 4 | Beide braid-realisaties falen directe ruimtelijke vergelijking |
| S32 | 4 | 4 | Alle vier `FLOOR_LIMITED`; **geen** gemeten ordebevestiging |
| S35 | 4 | 4 | Fremlin en Gilbert doorstaan core-robustheid |
| S37 | 4 | **0** | Mesh-gauge-certificatie mislukt |
| S40–S60 | 0 | 0 | Lege statusoutputs; geen trajectexperimenten uitgevoerd |
| Fase B trefoil | 0 eligible | 0 | `NOT_RUN_NO_S40_ELIGIBLE_RPO` |

Na S30 blijven dus **slechts twee** constructielijnen over. S10-diversiteit mag
niet gelezen worden als voldoende downstream-coverage.

S30 braid: maximale eindvormafstand 0.038697 en 0.040098 versus grens 0.02;
maximale trajectvormafstand 0.041868 en 0.043213 versus grens 0.025.

S37, met de bevroren vormgrens **0.035** en score-span-grens **0.12**:

| Kandidaat | Familie | Max. eindvormafstand | Score-span | Afkeur |
|---|---|---:|---:|---|
| C99F5F6CE155F28 | Fremlin | 0.021056 | 0.147977 | Mesh-stop vóór T=1.2 en score-span; niet de vormgrens |
| C3D2B0574EFE2FB | Fremlin | 0.038354 | 0.153810 | Mesh-stop, vormafstand en score-span |
| C1C51EE16EBC848 | Gilbert | 0.060364 | 0.019130 | Vormafstand |
| C2481D4C927839A | Gilbert | 0.062131 | 0.019239 | Vormafstand |

Ketenstatus: `CHAIN_CORE_ROBUST_SEEDS__MESH_GAUGE_NOT_CERTIFIED`.
De dichtstbijzijnde afzonderlijke metric is geen toestemming om andere gates
te negeren of de grens alsnog aan te passen.

## Fase B: wat nu werkelijk werkt

Nieuwe modules: `atlas.py`, `topology_witness.py`, `phase_b.py`, `campaign.py`.
De implementatie bevat:

- Full-state shooting in alle 3N-coördinaten, plus periode en return-transformatie.
- Dense full-state monodromy met centrale verschillen bij drie epsilons.
- Vast groeps-element, vaste referentievolume en vast tijdrooster tijdens de
  afgeleide; geen nieuwe normalisatie/Kabsch per verstoring.
- SVD-basis van translatie-, rotatie- en tijdsymmetrie; controle op invariantie,
  tijd-neutrale residual en volledige quotient-eigenwaarden.
- Gecontroleerde JVP/Arnoldi-route met expliciete partial-spectrum-status.
  Een deel van het spectrum bewijst geen stabiliteit van ongeziene modes.
  [SciPy-documentatie](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.eigs.html).
- Gepaarde baseline, identieke sham, halve core-feedback en fixed-core-ablation;
  de vooraf bepaalde primaire uitkomst is verandering van fixed-group return-RMS.
- Uitvoerbare 81-cellige N × dt × core × mesh-ladder. De echte trefoil-ladder
  wordt terecht niet gestart zonder eligible/nauwkeurige RPO.

### Engineering-metrologie, nadrukkelijk geen trefoil-evidence

Een translerende reguliere vortexring test de volledige route:

- N=8: volledige 24-dimensionale afgeleide; 6 onafhankelijke symmetry modes
  verwijderd en 18 quotient-modes berekend. Tijdtranslatie is hier redundant
  met ruimtelijke translatie, dus geen kunstmatig zevende mode.
- Return-RMS: `1.6059274338417866e-16`.
- Relatief verschil tussen FD-matrices: `2.285627140822074e-10`.
- Tijd-neutrale residual: `1.5847874420897038e-10`.
- Shamverschil: exact `0.0`; op deze constante-lengte-ring heeft de core-feedback
  ablation zoals verwacht geen meetbaar effect. Dit is een negatieve controle.
- N=8,12,16 × 12,24,48 tijdstappen: **9/9** analytisch gereconstrueerde
  ringcellen numeriek gevalideerd.
- Een apart negatief experiment dat de grove 8-hoek alleen interpoleert,
  in plaats van opnieuw een reguliere ring te construeren, blijft terecht
  `INDETERMINATE_INCOMPLETE_LADDERS`.

Geen van deze uitkomsten is een trefoil-stabiliteitsbewijs.

## Wat je nieuwe Knot Library v0.2.3-zip toevoegt

Archive SHA256: `f54551ccf1c9bd25b9cb236cf84abd9162fac2728d925b944747d5b86c7edd12`.
93 entries; 48 publieke track-campagnegeometrieën. De private seed en reveal in
de zip zijn niet geopend.

1. De 48 track-varianten zijn een 3×4×4 parametersweep van één constructiefamilie,
   niet drie onafhankelijke bronfamilies.
2. Pyknotid, Spherogram, SnapPy en KnotPlot werden in deze outputs niet beschikbaar
   gerapporteerd. Ridgerunner werd wel gevonden; aanwezigheid is geen uitgevoerde
   topologiecertificatie of onafhankelijke trefoil-dataset.
3. Fremlin: 402 bestanden ontdekt, **0 geselecteerd**, omdat onder meer 76 `.short`
   en 73 `.fseries` door het extensiefilter werden overgeslagen. Er zijn wel
   bruikbare geometrieën, die we rechtstreeks hebben ingelezen.
4. De brede KnotPlot-scan bevat ook omgevings-/supportbestanden. `OK` betekent
   niet automatisch “unieke, onafhankelijke, topology-certified trefoil”.
5. De seed suite en provider-/provenance-infrastructuur zijn bruikbaar voor
   constructie en audits, maar leveren niet vanzelf een strikte held-out atlas.

## Exacte uitgevoerde verificatie

Werkdirectory voor de packagecommando's:

`C:\workspace\projects\SST-Workbench\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier\SST_Trefoil_Dynamic_Seed_Qualification_Mega_Falsifier_v0.2.2`

```powershell
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -m pytest tests -q --basetemp 'C:\Users\oscar\Documents\Codex\2026-08-30\explore-x20\work\phaseb_pytest_final' --junitxml artifacts\tests_v022.xml --tb=short
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -m sst_seed_falsifier.selftest
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u -m sst_seed_falsifier.atlas freeze 'C:\workspace\projects\SST-Workbench' artifacts\prospective_atlas_20260830 --config config\prospective_atlas.json --protocol config\phase_b.json
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u -m sst_seed_falsifier.atlas generate-test 'C:\workspace\projects\SST-Workbench' artifacts\prospective_atlas_20260830
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u -m sst_seed_falsifier.campaign screen --repo 'C:\workspace\projects\SST-Workbench' --atlas artifacts\prospective_atlas_20260830 --out artifacts\blind_test_20260830 --config config\prospective_atlas.json
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -m sst_seed_falsifier.campaign phase-b --repo 'C:\workspace\projects\SST-Workbench' --atlas artifacts\prospective_atlas_20260830 --out artifacts\blind_test_20260830 --config config\prospective_atlas.json --protocol config\phase_b.json
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -m sst_seed_falsifier.campaign reveal --out artifacts\blind_test_20260830
```

De commando's hierboven documenteren de uitvoering; **herhaal freeze/generate
niet op dezelfde paden**. Ze weigeren bestaand bewijs te overschrijven.

Resultaten: **53 passed in 5.31s**, exitcode 0; native/Python relatieve L2-afwijking
**0.0**, selftest PASS. Tests zijn vóór de freeze uitgevoerd en na afloop opnieuw
uitgevoerd. De eerste testpoging zonder expliciete basetemp gaf 24 setup-errors
door Windows-toegang tot de standaard pytest-tempmap; 27 tests slaagden toen.
Met een nieuwe lokale tempmap slaagden alle tests. Dat was een omgevingsprobleem,
geen verzwegen modeltestfailure.

Losse audit-/metrologiescripts zijn uitgevoerd met dezelfde `.venv` vanuit
`C:\Users\oscar\Documents\Codex\2026-08-30\explore-x20`:

```powershell
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u work\audit_library_zip.py
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u work\phaseb_metrology.py
& 'C:\workspace\projects\SST-Workbench\.venv\Scripts\python.exe' -u work\collect_phaseb_results.py
```

Optionele pyknotid-installatie in een aparte werkmap is geprobeerd maar leverde
geen voortgang en is afgebroken. De bestaande repo-omgevingen zijn niet gewijzigd.

## Grenzen en aanbevolen vervolg

De implementatie is een werkende Fase-B-**basis**, geen voltooide publicatievalidatie.
Nog nodig zijn een nauwkeurige trefoil-RPO, daadwerkelijk geslaagde numerieke
ladders, branch-/spectrummatching over resoluties, gecontroleerde foutgrenzen,
topologiebehoud door de tijd, en gerepliceerde interventie-effecten met drie
overlevende constructielijnen. Causale taal blijft uitgeschakeld. Alle claims
blijven beperkt tot het **regularized filament / finite-core surrogate**.

De inhoudelijk juiste volgende stap is ontwikkeling op de nu verbruikte testset:
onderzoek de braid-resolutiefout en mesh-gauge-afhankelijkheid. Daarna pas een
nieuwe protocolfreeze en ongeziene reserve-/externe data. De huidige mislukkingen
rechtvaardigen geen aanpassing van S37 om deze run alsnog te laten slagen.

## Bijlagen

- [Machineleesbare campaign-evidence](C:/Users/oscar/Documents/Codex/2026-08-30/explore-x20/outputs/SST_v0.2.2_campaign_results.json)
- [Full-state-metrologie](C:/Users/oscar/Documents/Codex/2026-08-30/explore-x20/outputs/SST_v0.2.2_phase_b_metrology.json)
- [Audit van jouw v0.2.3-zip](C:/Users/oscar/Documents/Codex/2026-08-30/explore-x20/outputs/SST_Knot_Library_v0.2.3_zip_audit.json)

De broncode en alle lokale artifacts blijven in v0.2.2. De opleveringsbundel bevat
code, tests, configuratie en samenvattende evidence; geen reserve-seed, blind keys
of upstream/geometrie-herdistributie. De licentiestatus van Fremlin-data is daarmee
niet stilzwijgend als vrij beschikbaar behandeld.
