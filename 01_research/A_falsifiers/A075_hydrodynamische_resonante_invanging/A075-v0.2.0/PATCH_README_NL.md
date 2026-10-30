# A075-v0.2.0 pre-FREEZE compatibiliteitspatch v0.2.0-p1

Deze overlay corrigeert **alleen pakketintegratie** met Framework v1.0.10. Geen model-, meet- of wetenschappelijke statuspromoties. A075-v0.2.0 blijft DEVELOPMENT_ONLY.

## Bevestigde fouten
1. `tools/prepare_private.py`: de `preregistration` map ontbreekt; eerste poging schreef al `private/REVEAL_NONCE.bin`, `private/blind_forbidden_terms.txt`, `private/reveal.json`. De reparatie laat die drie bestanden ongewijzigd en maakt alleen de ontbrekende `OPAQUE_ID_KEY.bin` en twee echte nonced commitments aan.
2. `science_contract.json`: `steps` bevat strings, terwijl v1.0.10 objecten met `id`, `operation`, `formula_refs`, `gate` vereist.
3. `report/FALSIFIER_REPORT.tex`: de 16 verplichte `SST-REPORT-SECTION` markers ontbreken. Ook worden nu automatisch gegenereerde science-contract- en resultatenbijlagen geïmporteerd waar aanwezig.
4. Het oude private voorbereidingstool produceerde gewone SHA-256-bestanden; het framework vereist een domain-separated hash met nonce. Deze patch genereert het juiste formaat.

## Installatie / herstel op Windows
Unzip **over** de bestaande `A075-v0.2.0` projectmap (dus `science_contract.json` staat direct naast `run_all.cmd`; `tools/` en `report/` eronder). Bewaar de oude versies desgewenst als backup **buiten** de A075-bronmap zodat de blindscanner ze niet verwerkt. Laat bestaande `private/` en `preregistration/` ongewijzigd.

Uitvoervolgorde vanaf het projectroot:

```bat
python -m pytest -q tests
python tools\preflight_contract.py
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
```

**Stopregels:** als `preregistration/FROZEN_PROTOCOL.json` reeds bestaat, **niet** patchen of protocolbestanden aanpassen; maak een nieuwe campagne of versie. Als bestaande commitments incompleet/niet geldig zijn, eerst handmatig verifiëren; niet opnieuw secrets genereren. `PRIVATE/` of revealgegevens nooit in gedeelde ZIP.

De oorspronkelijke numerieke onder-resolutie en de vraag over duurzame energie-invanging blijven UNRESOLVED. Geen bewijs van langdurige retentie.
