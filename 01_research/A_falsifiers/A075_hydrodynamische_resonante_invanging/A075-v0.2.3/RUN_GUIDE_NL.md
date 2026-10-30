# A075 v0.2.3 — adaptieve tijdstap en backendmatrix

## Plaatsing
Pak het SOURCE-archief uit in `C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\`, zodat een **nieuwe** `A075-v0.2.3` naast bestaande versies ontstaat. Kopieer geen private keys, outputfolders of bestaande `FROZEN_PROTOCOL.json` mee. Het framework zelf staat onder `06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`.

## Installeren en controleren
```bat
cd C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A075_hydrodynamische_resonante_invanging\A075-v0.2.3
python -m pip install -r requirements.txt
python tools\build_native.py
python -m pytest -q tests
run_all.cmd BASIC --grid 80 --grid-up 112 --dt 0.015 --cfl 0.15 --threads 12 --backends py,cpp,gpu --allow-expensive --plan
run_all.cmd GPU_PROBE
```

De GPU-route gebruikt een op XPU geïnstalleerde PyTorch-versie. Installeer die via https://pytorch.org/get-started/additional-platforms/ (Windows / XPU). De Arc A770 is een ondersteund GPU-familielid, maar dat bewijst nog niet dat de noodzakelijke `torch.fft`-operaties op jouw specifieke installatie en precisie werken. `GPU_PROBE` test beide routes afzonderlijk: de SYCL-worker voor Biot–Savart en de echte PyTorch-XPU FFT-route.

## Bevriezen en BASIC-matrix draaien
```bat
python tools\preflight_contract.py
python tools\prepare_private.py
run_all.cmd FREEZE
run_all.cmd BASIC --grid 80 --grid-up 112 --dt 0.015 --cfl 0.15 --threads 12 --backends py,cpp,gpu --allow-expensive --require-all-backends
```

`--require-all-backends` weigert vóór de wetenschappelijke berekeningen als een backend niet beschikbaar is. Zonder die optie draaien de beschikbare backends door; de ontbrekende backend wordt **BLOCKED**, niet stilzwijgend CPU. De GPU-route met `--gpu-precision fp32` geeft uitsluitend screeningsbewijs. Voor `fp64` moet eerst aangetoond worden dat het apparaat dit ondersteunt.

Start met minder knopen als een eerste, afzonderlijke development-campagne gewenst is: `--knots 0_1,3_1`. De oorspronkelijke `5_2`/`6_1`-XYZ-geometrieën horen in `inputs/` en ontbreken anders bewust. Reproduceer een frozen run nooit met achteraf gewijzigde science-contractbestanden.

## Intensiteitspresets
- `PREVIEW`: 48^3 naar 64^3, T=0.6, maximale dt 0.020
- `BASIC`: 80^3 naar 112^3, T=1.2, maximale dt 0.015
- `EXTENDED`: 96^3 naar 128^3, T=3.0, maximale dt 0.012
- `FULL`: 96^3 naar 128^3, T=9.0, maximale dt 0.010

Opties `--grid`, `--grid-up`, `--dt`, `--t-end`, `--cfl`, `--max-core-shift`, `--max-vorticity-turn`, `--dt-min`, `--diagnostic-stride`, `--threads`, `--backends` en `--allow-expensive` worden als runtimekeuzen vastgelegd. De dynamische tijdstap wordt door de adaptieve controller *kleiner* dan de maximale dt waar nodig; na een RK4-stap wordt de snelheid nogmaals gecontroleerd en kan de stap worden herhaald met halve dt.

## Wetenschappelijk onderscheid
- **G0**: echte Framework v1.0.10 FREEZE en protocolbehoud.
- **G1**: bronprovenance; een ontbrekende oorspronkelijke knoop is een bronblokkade.
- **G2**: onafhankelijke tijd- en ruimtelijke screening; dit is niet de volledige continuümconvergentie.
- **G3**: pas bewijsbaar na vertrek donor, onafhankelijk klokbewijs en een vooraf vastgelegde 100-cycli-late-tail.
- **G4**: preregistreerde onafhankelijke holdout.
- **G5**: C++-hybride softwarepariteit kan worden gemeten, maar is nog geen onafhankelijk volledig-native C++-Eulerbewijs; hangt bovendien van G4 af.
- **G6**: echte GPU-Euler-pariteit vereist volledige apparaatuitvoering én gepaste precisie en kent prerequisieten. De framework SYCL-Biot–Savart-probe is niet G6.
- **G7/G8**: echte topologische XYZ/box/core/3D-continuümconvergentie.
- **G9**: reveal uitsluitend na gekwalificeerde vooraf gedefinieerde gates.

Het doel is adversarieel toetsen, **niet** alle gates kunstmatig PASS laten geven. De wetenschappelijke conclusie blijft `UNRESOLVED` tot zij onafhankelijk sluiten.

## Output
Per geometrie/backend/rooster:
`*_base_energy_matrix.csv`, `*_dt_half_energy_matrix.csv`, `*_space_up_energy_matrix.csv`; elk met fysieke tijd, dt, snelheid, vorticiteit, cellenverplaatsing, energie, per-stap numerieke energiedrift en afgewezen RK4-pogingen.
De lokale energie en drukflux worden apart in de gesamplede `timeseries` gezet.
`BACKEND_MATRIX.json`, `BACKEND_PREFLIGHT.json`, `SOLVER_SOURCE_HASHES.json` en Framework-manifests registreren het bewijs en de uitvoerbare bron.
