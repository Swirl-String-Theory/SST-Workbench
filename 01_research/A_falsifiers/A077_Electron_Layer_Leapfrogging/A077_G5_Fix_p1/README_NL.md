# A077-v0.1.1 — G5 native shape interface fix p1

## Diagnose

De `native/cpp/native.cpp`-binding retourneert de C++ `std::vector<double>`
van `ring_sst::integrate()` als een **platte** reeks met `(steps+1)*2*nrings`
waarden in tijdvolgorde. De Python-referentie `trajectory()['y']` heeft vorm
`(steps+1, 2*nrings)`. In `experiment/pipeline.py`, gate G5, ontbrak de
`reshape()`, wat altijd `ValueError('invalid native result')` geeft, zelfs
als de afzonderlijke waarden numeriek overeenkomen.

## Installatie (Windows, geen overschrijvende extractie)

1. Laat je bestaande `A077-v0.1.1/` intact; verwijder geen output, FREEZE of
   andere historie.
2. Pak deze ZIP uit als map **naast** de bestaande versie:
   `.../A077_Electron_Layer_Leapfrogging/A077_G5_Fix_p1/`.
3. Open cmd.exe in `.../A077_Electron_Layer_Leapfrogging/A077-v0.1.1/`.
4. Voer het volgende uit:

```cmd
..\A077_G5_Fix_p1\CHECK_PATCH.cmd
..\A077_G5_Fix_p1\APPLY_PATCH.cmd
python -m pytest -q tests
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

De patch weigert een onbekend gewijzigde `pipeline.py`, bestaande conflicterende
tests, een foutieve patchchecksum of een onvolledige frameworkruntime. Alleen
`experiment/pipeline.py` en een nieuwe regressietest worden geïnstalleerd.
De originele bron wordt **buiten** de versie opgeslagen in
`A077-v0.1.1_PATCH_BACKUPS/G5_p1_<timestamp>/pipeline.py.before`, naast
`PATCH_PROVENANCE.json` met de oude en nieuwe hashes.

### Wat deze patch *niet* doet

- Geen herbouw van `_sst_runtime/` of wijziging van het bronmanifest.
- Geen verandering van de Biot–Savart-, Euler- of RK4-berekeningen.
- Geen wijziging van `science_contract.json`, `gate_plan.json`,
  `FALSIFIER_REPORT.tex`, preregistratie, blind- of reveal-sleutels.
- Geen wijziging van het aantal backendcategorieën of toleranties.
- Geen claim dat elektronspin of discrete energielagen zijn afgeleid.

## Integriteits- en versiebeleid

Dit is een **gedocumenteerde source hotfix in development** na een
reeds geregistreerde FREEZE. Eerdere run-ID's behouden hun oorspronkelijke
provenance. Voor een formele wetenschappelijke release behoort de wijziging
in een nieuwe versie te worden opgenomen, bijvoorbeeld `A077-v0.1.2`, met
een nieuwe preregistratie en FREEZE. De hotfix voorkomt niet zelfstandig dat
bestaande code buiten de bevroren protocolbundle verandert; de externe
`PATCH_PROVENANCE.json` registreert deze wijziging afzonderlijk.

Een Windows-build is in deze omgeving niet getest; de C++17 commandlinekernel
is hier gecompileerd en numeriek tegen Python vergeleken, en de vier
interface-regressies zijn uitgevoerd.
