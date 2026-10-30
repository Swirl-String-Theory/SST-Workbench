# Voortgangscontract - Falsifier Framework v1.1.0 RC2

**Doel:** geen langdurig stilstaande `run_all.cmd`-uitvoering. Deze module geeft zichtbare checkpoints bij de wetenschappelijke pipeline, elk van de drie backendcategorieen, rapporteren en archiveren, met een onafhankelijke heartbeat na standaard **15 seconden** zonder afronding. De heartbeat wordt door een afzonderlijk Python-proces uitgegeven en werkt daardoor ook als een native C++/pybind11-kernel de interpreter blokkeert.

## Bedieningscontract

- `run_all.cmd FULL` start standaard `progress_supervisor.py` met de omgeving die door `SST_PYTHON` is geselecteerd; de oorspronkelijke return-/exitcode blijft ongewijzigd.
- Voortgang wordt onmiddellijk als `[SST][PROGRESS]` op het scherm getoond; `[SST][HEARTBEAT]` meldt elke 15 seconden dat het proces nog actief is, inclusief actuele fase en, alleen indien werkelijk bekend, `completed/total`.
- Een heartbeat is **geen** bewijs dat het numerieke algoritme nog vooruitgaat. Een vastgelopen solver kan heartbeat blijven tonen; stel wetenschappelijke time-outs en stopcriteria apart vast.
- Tijdens een `FULL`-run wordt `RUN_PROGRESS.jsonl` in de unieke outputdirectory aangemaakt en opgenomen in de immutable evidence- en outputmanifesten. Het log wordt **voor** het maken van deze manifesten gesloten. De fasen voor rapportgeneratie en ZIP-publicatie blijven wel zichtbaar in de console, zonder het bevroren log te muteren.
- Stel de frequentie in met `set SST_PROGRESS_HEARTBEAT_SECONDS=10`. Standaard 15 s; maximaal 3600 s. Een waarde onder 15 s is zinvol bij interactieve onderzoeken; gebruik niet voortdurend spammy output.
- Bij afsluiten met exitcode `3` wegens ontbrekende 2-uit-3-bewijzen of een andere wetenschappelijke gate, mag de monitor **nooit** een `PASS` suggereren.
- `run_instance.py` direct uitvoeren geeft dezelfde fase-events en een thread-heartbeat; voor native code die lang de Python GIL vasthoudt verdient **`run_all.cmd`** de voorkeur.

## Aanbevolen code in nieuwe falsifiers

```python
from sst_falsifier import progress

# Backendopdrachten. De A999-adapter implementeert dit al:
for index, kind in enumerate(('py','cpp','gpu'),start=1):
    with progress.phase('BACKEND',completed=index-1,total=3,backend=kind):
        run_real_kernel(kind)

# Ruimtelijke verfijningen - zelfde fysische eindtijd en consistente kernregularisatie.
for i, N in enumerate((128, 256, 512),start=1):
    with progress.refinement('spatial',level=i,total=3,resolution=N,final_time=1.0):
        run_at_resolution(N)

# Temporele verfijningen - zelfde fysische eindtijd, kleinere tijdstap.
for i, dt in enumerate((0.01,0.005,0.0025),start=1):
    with progress.refinement('temporal',level=i,total=3,dt=dt,final_time=1.0):
        run_with_step(dt)
```

De binnenste `progress.refinement`-context laat `level`, `completed`, `total` en de gekozen resolutie/tijdstap zien. Deze waarden zijn labels van de daadwerkelijk geplande taak, geen schattingen van numerieke convergentie. Het voortgangscontract vervangt geen ruimtelijke of temporele convergentiegates.

## Beveiliging en reproduceerbaarheid

Het openbare voortgangslog bevat alleen fase, status, tijdstempel, runtijd, backend, verfijningsindex en toegelaten metadata (`resolution`, `dt`, `final_time`). Schrijf geen blinde targets, private revealing-sleutels, ongekwalificeerde wetenschappelijke conclusies of absolute gevoelige bronpaden naar voortgangsevents. De tijdelijke heartbeat-statefile wordt buiten het auditarchief geschreven en na afloop verwijderd. Bron- en resultaat-hashes blijven de autoriteit voor geldige wetenschappelijke uitvoer.

## Windows RC2-acceptatietest (behoud RC1)

```cmd
set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
set "SST_PYTHON=%WB%\.venv-a075-xpu\Scripts\python.exe"
set "SST_PROGRESS_HEARTBEAT_SECONDS=15"
cd /d "%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.1.0_RC2"
tools\run_a999_rc2_acceptance.cmd "%TEMP%\SST_A999_E010_trefoil_18736"
```

Deze opdracht gebruikt de eerder geverifieerde E010-export, creeert een **nieuwe** tijdelijke A999, controleert alle regressietests, voert `FREEZE`, `FULL` en de onafhankelijke auditor uit, en schrijft het acceptatiebestand **buiten** de gehashte runoutput. Als een gate faalt, blijft de output behouden en krijgt de uitvoer een niet-nul-exitcode. RC1 blijft ongewijzigd.
