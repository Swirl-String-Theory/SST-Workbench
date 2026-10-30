# Euler Trajectory Resolution Generator v0.2.0

**Zelfstandig numeriek hulpmiddel voor A075 en A077** — onafhankelijke Euler-trajectverfijning, kern- en boxgevoeligheid en veldperturbaties. Dit pakket **wijzigt geen bestaande bevroren falsifierversie** en is niet fysisch gecertificeerd. De providercontrole is fail-closed en accepteert uitsluitend de vooraf gepinde solverbronnen van A075-v0.2.9/v0.2.10 en A077-v0.1.2. De volledige A075 Ruban-geometriedata zijn daarnaast verplicht; de generator maakt geen vervangende seeds.

## Kernverbeteringen ten opzichte van v0.1.0

1. Twee profielen plus een smoketest: `smoke` (16/24/32, uitsluitend software), `pilot` (48/64/96), `qualification` (automatisch berekende kernresolutieladder).
2. Vijf *gescheiden* studies: `spatial`, `temporal`, `core`, `box`, `perturb`, met een vast fysisch model-eindtijdstip en expliciete parameterbeheersing.
3. `--effective-resolution` kan de planningsdrempel verstrengen met een heuristische factor 3/2 vanwege de 2/3-spectrale afsnijding. Dat is geen gelijkwaardige definitie van de effectieve fysische roosterafstand.
4. De periodieke boxlengte en de regularisatiebreedte kunnen onafhankelijk worden gewijzigd. Voor A075 verandert `--core-factor` de Gaussian-smoothingbreedte, **niet** de geometrische Ruban-minorradius. Voor A077 verandert de factor de initiële ringkernradius in de inputkopie.
5. Automatische vergelijking van ongewrapte materiële tracerpunten op overeenkomende fysieke tijden, behoudsdiagnostiek, run-hashes, integriteitscontrole, uitvoerlogboeken en een ZIP+SHA256 per campagne.
6. Een uitvoeringsplan wordt standaard *alleen* gegenereerd. `--execute` is vereist; te zware runs worden vooraf geweigerd of expliciet als `SKIPPED_MEMORY_PREFLIGHT` vastgelegd.

## Installatie

Pak de ZIP uit **naast** bestaande versies, bijvoorbeeld:

```text
C:\workspace\projects\SST-Workbench\04_tools\A_geometry\EulerTrajectoryResolutionGenerator_v0.2.0\
```

```bat
python -m pip install numpy scipy pytest
python verify_source.py
python -m pytest -q tests
```

Gebruik volledige paden naar originele A075 en A077 bronnen. De generator kopieert, reset of overschrijft geen bestaand experiment.

## 1. Plan voorbereiden (geen zware berekening)

```bat
run_studies.cmd --a075-root "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.10"  --a077-root "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.2" --profile qualification --studies all --memory-limit-gib 16
```

Dit schrijft `RUN_PLAN.json` met resulterende NxNxN-niveaus, bronhashes, geheugenschatting en afzonderlijke parameterassen. Alleen wanneer de begroting en de bronintegriteit acceptabel zijn, voer uit:

```bat
run_studies.cmd --a075-root "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.10"  --a077-root "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.2"  --profile qualification --studies all --memory-limit-gib 32 --execute
```

**Let op:** bij `--profile qualification --studies all` zijn de ruimtelijke niveaus **allemaal minstens vier nominale kerncellen per radius**: A075 `260³,312³,364³`, A077 `170³,204³,238³`. De A075-ladder kan boven 85 GiB RAM uitkomen (en strenger met `--effective-resolution`); ook de 1,25× boxvariant is zwaar. De basis `260³` vereist naar schatting circa 31 GiB. De geheugenschatting is indicatief; beschikbaar RAM en swap vooraf controleren. Gebruik `--skip-unaffordable` om andere studies gecontroleerd uit te voeren; de campagne krijgt dan de status `PARTIAL_INCOMPLETE`, nooit PASS. `--allow-memory` is alleen voor experts die bewust het veiligheidshek negeren.

## 2. Snelle verkenning (niet gekwalificeerd)

```bat
run_studies.cmd --a075-root "C:\...\A075-v0.2.10" --a077-root "C:\...\A077-v0.1.2" --profile pilot --studies spatial temporal --time 0.02 --dt 0.001 --markers 24 --execute
```

Of één provider / één studie:

```bat
run_studies.cmd --providers a077 --a077-root "C:\...\A077-v0.1.2" --profile qualification --studies spatial --time 0.02 --dt 0.001 --markers 32 --memory-limit-gib 16 --execute
```

Voor een strengere planning (niet automatisch uitvoerbaar op werkstation):

```bat
run_studies.cmd --a075-root "C:\...\A075-v0.2.10" --a077-root "C:\...\A077-v0.1.2" --profile qualification --effective-resolution --studies spatial
```

## 3. Wat is de noodzakelijke ruimtelijke resolutie?

Bij een vereiste van ten minste vier **nominale** roosterafstanden per geometrische radius, in de gekozen periodieke box:

| Provider | Relevante straal | Box L | Nominale N-drempel | Heuristische 2/3-bandlimiet-drempel |
|---|---:|---:|---:|---:|
| A075 Ruban | 0.154 | 10 | 260 | 390 |
| A077 kleinste ringcore | 0.19 | 8 | 170 | 254 |

De hogere `390³` en `254³` niveaus zijn door dit pakket **gepland maar niet werkelijk uitgevoerd**. Zelfs wanneer de numerieke grid-drempel zou slagen, blijven materiaalkernvalidatie, vormbehoud, periodieke-box-artefacten, vorticiteitsflux en onafhankelijke veldsolvers noodzakelijk.

## 4. Precies welke controles gelden?

- **Ruimtelijke ladder**: minstens drie N, met dezelfde box, fysische core/seed, eindtijd en dt. Vergelijk over de volle tijd de ongewrapte trajecten en eindposities. Ruimtelijke convergentie is slechts een proxy voor veld- en tracerconvergentie.
- **Temporele ladder**: gelijke N, kern/box/tracers, `dt,dt/2,dt/4` en gelijke eindtijd. Vergelijk op identieke absolute tijdcoördinaten; een screen van <0.02 kernradius eindverschil en verfijningsratio <0.75 is technisch verkennend, niet fysisch.
- **Kernbreedte**: smoothingprofielen 0.8/1.0/1.2×; de geometrische A075-kern blijft 0.154. Dit is **modelgevoeligheid**; variatie van de kernradius is niet een convergentie naar een unieke fysieke kern.
- **Boxgrootte**: 0.75/1.0/1.25× en ongeveer gelijk gehouden Δx door N mee te schalen. Vergelijk periodieke beeldeffecten zonder de ringgeometrie zelf te schalen.
- **Perturbatie**: één ongestoorde baseline en twee amplitudes (0.005 en 0.02) met elk drie gescheiden deterministische seeds, toegepast op het volledige divergentievrije Fourier-veld; geen gebruik van onafhankelijke markers als replicaten.

Outputs: per run `trial_0000/trajectory.npz` (tijd, positie, snelheid, origineel solverstelsel plus optionele SI-schaal), `conservation.csv`, `diagnostics.json`, `RUN_MANIFEST.json`, `OUTPUT_MANIFEST.json`; per studie `RUN_PLAN.json`, `RUN_LEDGER.json`, `EVALUATION.json`, `CAMPAIGN_STATUS.json`, campagne-ZIP en SHA256. Foutieve hashes, niet-eindige getallen en kritieke Courant-getallen (CFL) stoppen de betreffende run.

## 5. Onafhankelijke fysieke falsificatie blijft nodig

Dit is een **driedimensionaal spectraal Euler-veld** met passieve tracers, maar geen bewezen, getraceerde **materiële wervelkern**. Een verdwijning van trajectverschillen of een behoud van energie/heliciteit is geen bewijs voor dynamisch zelfherstel. De kleinste kern, de vorticiteitstangentie op een materieel oppervlak, circulatie rond materiële lussen, gerichte externe perturbaties, topologische isotopie en onafhankelijk veldvergelijk moeten apart worden gecertificeerd. De A068-variant voor materiële oppervlakken moet niet door de V1-tracers worden vervangen. Spin-1/2, elektronenidentiteit en SST-klokgedrag blijven expliciet `UNRESOLVED`.

Zie `docs/STUDY_PROTOCOL_NL.md`, `docs/RESULTS_NL.md`, `docs/COMPATIBILITY_AUDIT_NL.md` en de originele providerbronhashes. Beschikbare studies zijn uitgevoerd op Linux voor kleine smokeroosters; de Windows/groot-N-uitvoering is nog niet gevalideerd.
