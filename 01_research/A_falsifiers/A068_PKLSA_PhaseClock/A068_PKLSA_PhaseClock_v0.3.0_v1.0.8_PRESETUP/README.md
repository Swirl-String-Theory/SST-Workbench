# A068 v0.3.0 — vooraf ingestelde versie (Framework v1.0.8)

Dit is een **installatie-/bootstrapupdate van v0.3.0**: alle wetenschappelijke `overlay/`-bestanden zijn byte-identiek aan de eerdere distributie. Geen wijziging van de bevroren wetenschappelijke hypothesen, gates, numerieke parameters of reveal-policy. Dit pakket wijzigt het framework v1.0.8 niet.

## Eén opdracht

Uitpakken, daarna op Windows **dubbelklikken `SETUP_A068.cmd`** (of vanaf de geactiveerde project-venv `python setup_A068.py`). De gebruikelijke Workbench-locatie is al ingesteld: `C:\workspace\projects\SST-Workbench`.

De helper doet achtereenvolgens:

1. SHA-256 van distributie en broncode controleren;
2. JSON-schema, niet-ingevulde velden, brononafhankelijkheid, alle 16 LaTeX-reportsecties en de gate-DAG controleren;
3. met de **officiële v1.0.8-generator** een nieuwe A068-v0.3.0 instantiatie maken als er nog geen instantie bestaat; bestaande instanties worden niet overschreven;
4. de generieke framework-README (alleen als die aantoonbaar standaard/ongewijzigd is en de instantie nog NIET bevroren is) vervangen door een A068-specifieke handleiding;
5. de gegenereerde private nonce/HMAC-sleutels controleren (niet exporteren);
6. 17 A068-regressietests uitvoeren;
7. op de Windows-machine de **echte** `run_all.cmd FREEZE` starten en het gegenereerde `preregistration/FROZEN_PROTOCOL.json` controleren.

Een reeds bevroren instantie wordt **uitsluitend gecontroleerd**; er vindt geen nieuwe freeze of sleutelrotatie plaats. Als wetenschappelijke overlaybestanden in de bestaande instantie zijn veranderd, stopt setup zonder ze te herstellen of te overschrijven. Als je al hebt gefreezed, blijven alle bestaande outputs behouden.

Alternatieve opdrachten:

```cmd
python setup_A068.py --verify-only
python setup_A068.py --no-freeze
python setup_A068.py --workbench-root D:\Projects\SST-Workbench
```

De stap `FREEZE` kan niet vooraf op een andere computer namens jouw lokale frameworkinstallatie worden voltooid, omdat het bevroren protocol exact gebonden is aan lokaal gegenereerde private commitments en de instantie op jouw machine. De automatische helper voert die stap daarom **daar** uit; er is geen handmatige voorbereiding van stap 1-5 nodig.

## Wetenschappelijke uitkomst

BASIC/FULL/CERTIFY blijven operationeel als numerieke 3D-Euler-modeltests. `G3=UNRESOLVED` en de downstream-`NOT_RUN_PREREQUISITE` statussen zijn bewust en onveranderd. `REVEAL_IF_ALLOWED` blijft terecht fail-closed totdat er onafhankelijke, gekwalificeerde PKLSA-dynamica beschikbaar is. De setup **mag deze eis niet verzwakken**.

Meer inhoud: zie `FALSIFIER_REPORT_PREVIEW.pdf` en na installatie `report/FALSIFIER_REPORT.tex`.
