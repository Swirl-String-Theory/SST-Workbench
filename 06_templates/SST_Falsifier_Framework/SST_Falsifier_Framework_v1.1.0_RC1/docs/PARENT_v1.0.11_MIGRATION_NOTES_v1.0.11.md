# Framework v1.0.11 — technische migratienotities

## Ontwerpbesluit

Deze versie activeert een **automatische drie-backend preflight** bij iedere blind-science-run; voor werkelijke drie-backend-wetenschap moet de falsifier een expliciete `experiment/backend_matrix.py`-adapter bieden. Onbekende of ontbrekende implementaties krijgen **NO IMPLEMENTATION**, nooit een PASS. Geen automatische CUDA/Arc/CPU-fallback.

## Wijzigingen

1. `sst_falsifier/auto_backend_matrix.py`: CPU-FFT/NumPy, gecompileerde pybind11-aanwezigheid, torch-XPU-FFT-probes, vastgelegde statussen.
2. `sst_falsifier/runner.py`: schrijft `AUTO_BACKEND_MATRIX.json` in de bestaande outputroot na de wetenschappelijke pipeline, vóór het science-evidence-manifest. Nieuw `BACKEND_PREFLIGHT`-commando.
3. `sst_falsifier/sycl_worker.py`: `_src` zoekt bij een framework-root ook onder `instance_template/native/cpp/sycl_worker.cpp` als de normale instancebron ontbreekt.
4. Nieuwe `instance_template` krijgt exact v1.0.11-pinning en `[auto_backends]` met veilige defaults.
5. Oude freeze-/manifestbestanden worden in de nieuwe map gearchiveerd, niet als nieuwe certificatie hergebruikt.

## Garanties

- Framework v1.0.10 blijft op schijf ongemoeid.
- Frozen protocolbundels uit oudere falsifiers worden niet gewijzigd.
- De bestaande Python-science-pipeline, gate-uitkomsten en kernalgoritmen worden niet herschreven.
- `AUTO_BACKEND_MATRIX.json` vormt software-evidence, geen automatisch fysisch bewijs.
- Een wetenschappelijk adapterresultaat wordt slechts `EXECUTED_UNQUALIFIED` bij geverifieerde geclaimde uitvoering + bronhash; onafhankelijk numeriek PASS en fysische gates blijven aparte acceptatiecriteria.

## Risico's / acceptatie

- Deze patch is **niet** een op jouw Windows-machine uitgevoerde full-framework release-test.
- Een C++-probe valideert niet de inhoud/pariteit van de native extensie en controleert slechts een ABI-passende gecompileerde module.
- De GPU-probe test uitsluitend FP32-FFT op XPU; dit is geen solver- of FP64-certificatie.
- Bestaande falsifiers hebben een expliciete migratie naar een nieuwe frameworkpin nodig. Een `FREEZE` op het oude protocol mag niet alsnog achteraf gewijzigd worden.
