# Euler Trajectory Resolution Generator v0.1.0

**Ontwikkelingshulpmiddel / onafhankelijk exportinstrument voor A075 en A077.** Dit is **geen nieuw gecertificeerd Euler- of SST-fysisch resultaat**, en geen nieuwe versie van die bestaande, bevroren falsifiers. De exporter wijzigt hun bronbestanden, protocolhashes en gates niet.

## Wat is werkelijk geïmplementeerd?

- Twee geverifieerde, bron-gepinde adapters: **A075-v0.2.9/0.2.10 `experiment.euler3d`** en **A077-v0.1.2 `science.euler_field`**.
- Resoluties `48³`, `64³`, `80³`, `96³` (even N vanaf 16 voor smoke); dezelfde numerieke Euler-veldvergelijking als de bronprovider, zonder transformatie naar filament-ODE's.
- Volledig **mee-geïntegreerde passieve tracerpunten** door alle vier de veld-RK4-stadia; periodieke interpolatie, ongewrapte posities, vectoriële snelheid op ieder bewaard Euler-tijdstip.
- `run_dual.cmd` voert alle vier N voor beide providers sequentieel uit, zonder tegelijk twee zware 3D-velden in RAM te houden.
- Eén solverrecord per run met volledig geëxporteerde 3D-positie en snelheid (`trial_0000/trajectory.npz`), `conservation.csv`, kwaliteitscontrole, bron/manifesthashes en ZIP plus SHA256; campagnearchief met alle runarchieven.
- Eén **vaste fysieke simulatie-eindtijd** en één **vaste tijdstap** in de duale ruimtelijke ladder. Een aparte `--temporal`-optie voert alleen `dt, dt/2, dt/4` uit bij vaste N; combineer ze niet in een fysische convergentieclaim zonder extra materiaal-, box-, kern- en vormtests.
- Onafhankelijke solenoïdale perturbatie-seeds per *volledige veldrealisatie*, als `--trials > 1 --perturb p` expliciet gekozen is. Verschillende N zijn géén onafhankelijke experimenten.
- Hergebruik van A026's RK4-concept, maar een aangepaste **vectoriële, veeltracer- en twee-provider-interface**. De uitvoer is bewust NIET identiek aan het A026 `q_m, qdot_m_s`-intakeformaat; voor A026 moet een aparte adapter met trajectonafhankelijkheidscontrole worden gebruikt.

## Installatie (Windows 11, Python 3.13 ondersteund)

Pak dit pakket **buiten** de bestaande A075/A077-versiemappen uit, bijvoorbeeld:

```
C:\workspace\projects\SST-Workbench\04_tools\A_geometry\EulerTrajectoryResolutionGenerator_v0.1.0\
```

Voor de primaire solvers zijn nodig: `python -m pip install numpy scipy pytest`. Controleer eerst de generator zelf met `python verify_source.py` en `python -m pytest -q tests`.

De hiernaast genoemde A075-bronnen komen uit **A075-v0.2.9 en v0.2.10**. Een A075-v0.2.14-addon is géén identieke volledige Euler-solverrelease. De twee gepinde A075-modules zijn in v0.2.9 en v0.2.10 exact gelijk; andere versies weigert de generator bij bronhash-afwijking.

### Voor beide providers en alle vier N

Vanuit de generatormap:

```bat
run_dual.cmd "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.10" "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.2"
```

Controleer de **werkelijke lokale A075-mapnaam**: Windows-paden en case kunnen afwijken van de voorbeeldspelling. De A077-root is exact de versie-directory met `science/euler_field.py`. Dit script draait A075 `ruban` en A077 `toroidal_plus`, N=48,64,80,96, met vaste `t_final=0.02`, `dt=0.001`, 12 passieve tracers. Dit is een **software-/korte dynamische pilot**, niet het volledige lange traject- of continuum-certificatieprotocol.

### Andere A077-toroïdale gevallen of lange looptijd

```bat
run_generator.cmd --provider a077 --source "C:\...\A077-v0.1.2" --grid 96 --case no_toroidal --time 0.02 --dt 0.0005 --markers 32
run_generator.cmd --provider a077 --source "C:\...\A077-v0.1.2" --grid 96 --case toroidal_minus --time 0.02 --dt 0.0005 --markers 32
```

### Alleen A075 + 96³

```bat
run_generator.cmd --provider a075 --source "C:\...\A075-v0.2.10" --grid 96 --geometry ruban --time 0.02 --dt 0.0005 --markers 32
```

### A075/A077 temporele ladder bij vaste N

```bat
run_generator.cmd --provider a077 --source "C:\...\A077-v0.1.2" --grid 96 --case toroidal_plus --temporal --time 0.02 --dt 0.001
```

Daarna vergelijken we op hetzelfde eindtijdstip tussen `dt=0.001,0.0005,0.00025`; de gewone `--all` gebruikt N=48,64,80,96 met dezelfde dt.

### 4×4 ruimtelijke/case-studie (A077)

```bat
python -m resolver.campaign --a075-root "C:\...\A075-v0.2.10" --a077-root "C:\...\A077-v0.1.2" --a077-cases no_toroidal toroidal_plus toroidal_minus --grids 48 64 80 96 --time 0.02 --dt 0.001 --markers 12
```

**Geheugen:** de veldintegratie gebruikt meerdere reële en complexe 3D-arrays. `96³` kan meerdere GiB piekgeheugen vragen; de schatting is indicatief en de generator heeft een instelbare geheugen-waarschuwingsgrens. Het is geen GPU-kernel: Intel Arc A770 wordt **niet** gebruikt en preflight telt niet als wetenschappelijke backend. Eén provider per proces; varianten sequentieel.

## Documenteerde beperking bij N=96

| Grid | A075 Gaussian sigma=0.42, L=10 (sigma/dx) | A075 Ruban r_minor=0.154, L=10 (radius/dx) | A077 min a=0.19, L=8 (a/dx) |
|---:|---:|---:|---:|
| 48³ | 2.016 | 0.739 | 1.140 |
| 64³ | 2.688 | 0.986 | 1.520 |
| 80³ | 3.360 | 1.232 | 1.900 |
| 96³ | 4.032 | 1.478 | 2.280 |

De Gaussian-smoothingbreedte van A075 is **niet hetzelfde** als de geometrische Ruban-radius. Dit laatste blijft ook bij N=96 kleiner dan 1,5 roosterafstanden. Een veel gebruikte verkennende drempel van 4 punten per radius zou voor de Ruban-geometrie met L=10 ongeveer N≥260 vragen en voor A077 min a=0.19, L=8 ongeveer N≥170. Dit zijn **geen** gegarandeerde continuumcriteria: bij 2/3-dealiasing, tracerinterpolatie, veldcontacten en periodiciteit kunnen strengere eisen gelden.

## Alleen observabelen, geen automatisch bewezen fysica

`positions_unwrapped_solver`: traject van passieve vloeistofmarkers.
`velocity_solver`: op ieder veldtijdstip de lokale Euler-snelheid.
`times_solver`: absolute model-evolutietijd in genormaliseerde solvereenheden.
`positions_m`, `velocities_m_s`, `times_s`: schaalomzetting met expliciet gekozen `--length-unit-m`, `--speed-unit-m-s`, **geen fysisch gemeten electron/r_c/clock**.
`conservation.csv`: energiescreen, heliciteit, divergentie en enstrofie van het periodieke, getrunceerde Euler-model.
`OUTPUT_MANIFEST.json` en `.zip.sha256`: reproduceerbare bron-/uitvoercontrole.

**Verplicht voor een fysieke promotie:** (1) onafhankelijke ruimtelijke en temporele continuümladders, (2) kernbreedte en boxgrootte, (3) tracerinterpolatiefout, (4) expliciete materiële oppervlakte/kerntopologie en vorticiteitstangentie, (5) perturbaties, (6) onafhankelijke bron/solver, (7) voor spin afzonderlijk afgeleide toestandsruimte en 2π/4π-holonomie. `PASS` voor code-integriteit is niet de fysieke gate G8.

Zie `docs/COMPATIBILITY_AUDIT_NL.md` voor de vier gegevensvarianten en de geschikte projectfamilies.

**Integriteit:** de bron-ZIP bevat uitsluitend de nieuwe exporter en auditdocumentatie. De oorspronkelijke A075/A077-solvers, privé-revealsleutels en oude BLIND-data worden niet meegenomen. Het aanvullende `SOURCE_FILE_MANIFEST.json` controleert de eigen bestanden, zonder de SHA-256-contracten in A075/A077 te veranderen.
