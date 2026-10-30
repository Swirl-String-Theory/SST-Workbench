# A075-v0.2.9 — installatie en testinstructies (Windows)

Plaats de complete versie `A075-v0.2.9` naast v0.2.7 in `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\`.
Gebruik de bestaande `.venv-a075-xpu` voor PyTorch XPU + NumPy/SciPy/pytest/pybind11.

```bat
cd C:\workspace\projects\SST-Workbench
.venv-a075-xpu\Scripts\activate.bat
cd 01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.9
python -m pip install -r requirements.txt
python -m pytest -q tests
python tools\check_sources.py
python tools\verify_ruban.py
run_all.cmd RUBAN_PREVIEW --grid 24 --grid-up 32 --t-end 0.04 --dt 0.01 --threads 12 --heartbeat-seconds 10
```

Deze `RUBAN_PREVIEW` is een **lokale niet-bevroren** screening met twee bronvrije trefoils. De uitkomsten staan in `ruban_diagnostics/<unieke_run_id>/`, niet in een officieel frameworkuitvoerarchief. Geen backendkwalificatie.

Na succesvolle preflight voor formele uitvoer via Framework v1.1.0:

```bat
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --ruban-study --grid 80 --grid-up 112 --t-end 1.2 --dt 0.015 --threads 12 --allow-expensive --heartbeat-seconds 10
```

Dit laat de standaarddonor-suite met rust: de eigen Ruban-study doet een enkele bronvrije T(2,3) plus B0=0.32 controle. Het framework draait daarnaast werkelijk Python, C++ en GPU op de Ruban-input waar beschikbaar. Pas `--ruban-refinement` toe als een **expliciet optionele zwaardere** tijd- en roostervergelijking gewenst is:

```bat
run_all.cmd BASIC --ruban-study --ruban-refinement --grid 80 --grid-up 112 --t-end 1.2 --dt 0.015 --threads 12 --allow-expensive --heartbeat-seconds 10
```

Controleer live vanuit een tweede venster: `run_all.cmd STATUS`.

**LET OP**: dat Ruban filamentregularisatie `delta=0.05` en `Lambda~4.049` kent, betekent niet dat de Euler Gaussian sigma 0.05 moet zijn. De standaard sigma 0.5 geeft 4 cellen per sigma bij N=80, maar smeert de kleine Ruban torusradius 0.154 sterk uit. Proeven met coreverfijning zijn daarom nog geen getrouwe Ruban-modelreproductie. Rooster-, core- en doosverfijningen plus materiële topologietracking blijven noodzakelijk; G12/G8 UNRESOLVED.

De `--plan`-vlag voert niets uit. Zonder `--ruban-study` blijft gewone `BASIC` exact de bestaande donor/capture-suite.

## Optionele referentie voor Rubans eigen filamentvergelijking

```bat
run_all.cmd RUBAN_FILAMENT --filament-points 128 --filament-t-end 0.04 --filament-dt 0.005 --heartbeat-seconds 10
```

Dit is een onverkorte, aparte **ontwikkelvergelijking**, niet de oorspronkelijke auteursintegrator. `--ruban-filament` kan optioneel aan een officiële `BASIC --ruban-study` worden toegevoegd, voor G13-diagnostiek (niet voor fysische PASS).
