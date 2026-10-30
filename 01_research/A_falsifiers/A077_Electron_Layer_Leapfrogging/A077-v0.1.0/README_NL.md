# A077 v0.1.0 — gerichte runtimeherstelpatch p1

## Exacte oorzaak
In het eerder uitgeleverde bronarchief zijn **twee bronbestanden weggelaten** door de exportfilter. Het ingebedde manifest verlangt 142 bestanden, maar slechts 140 zijn aanwezig. De 140 bestaande bronbestanden hebben correcte hashes. Dit is geen newline-/Windows-/compilerfout.

Ontbrekend:
- `_sst_runtime/sst_falsifier/outputs.py` (7095 bytes)
- `_sst_runtime/tests/test_outputs.py` (1074 bytes)

Deze patch bevat identieke bronbytes uit het oorspronkelijke geverifieerde Framework v1.1.0-archief. **Geen bestaande bestanden, protocollen of manifests worden gewijzigd.** Er is geen herhash- of acceptatie-bypass.

## Installatie
1. Maak een veiligheidskopie van de A077-v0.1.0-map inclusief reeds aanwezige `*-outputs` en `/private`.
2. Pak **de map** `A077-v0.1.0_Runtime_Restore_p1` uit in `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.0`.
3. Open de oorspronkelijke A077-v0.1.0-opdrachtprompt en voer uit:

```bat
A077-v0.1.0_Runtime_Restore_p1\APPLY_RESTORE.cmd
python -m pytest -q tests
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

Of, als `py -3` niet beschikbaar is:

```bat
python A077-v0.1.0_Runtime_Restore_p1\repair_runtime.py --instance .
python A077-v0.1.0_Runtime_Restore_p1\repair_runtime.py --instance . --verify-only
```

Bij een ander hashprobleem weigert het script herstel; de originele inhoud wordt **nooit overschreven**. De uitslag `142/142` betreft alleen runtime-integriteit; het is **geen** fysische gate-PASS. Nieuwe runs behouden hun unieke identificaties conform frameworkbeleid. Gebruik voor bestaande bevroren protocollen nooit ongecontroleerde manifestwijzigingen.

## Provenance
De bestands-SHA-256's zijn verankerd in het ongewijzigde `_sst_runtime/RUNTIME_SNAPSHOT_MANIFEST.json`. De twee bronbestanden zijn byte-exact met de canonieke Framework-bron vergeleken.
