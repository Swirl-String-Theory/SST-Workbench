# SST Falsifier Framework v1.0.11 — Installatiehandleiding (Windows 11)

**Release:** ontwikkelupgrade op basis van een lokaal bestaande, ongewijzigde v1.0.10.  
**Doel:** bij iedere nieuwe blind-science-run automatisch Python, C++ en Intel XPU controleren; indien aanwezig een *falsifier-specifieke* wetenschappelijke backend-adapter uitvoeren. Niet-geïmplementeerde wetenschappelijke backends worden **NIET** als PASS gemarkeerd.

## 1. Wat is daadwerkelijk bewezen op jouw machine?

Volgens de aangeleverde logs van 28 oktober 2026:

- Python 3.14.3;
- `.venv` bevatte eerst `torch 2.12.1+cpu`, XPU `False`;
- afzonderlijke `.venv-a075-xpu` is succesvol geïnstalleerd met `torch 2.12.1+xpu`;
- `torch.xpu.is_available()` retourneerde `True`, apparaatentelling 1;
- `torch.fft.fftn` op `xpu:0` retourneerde `torch.complex64` voor een array van 32³;
- bestaande C++/pybind11/OpenMP-extensie bouwde onder MSVC 2022, Python ABI `cp314-win_amd64`;
- Framework v1.0.10's SYCL-Biot–Savart-worker detecteerde de Intel Arc A770, maar GEEN native FP64.

**Niet bewezen:** volledige Eulerberekening op de GPU, nauwkeurigheidspariteit van 3 fysische solvers, of algemene wetenschappelijke gate-PASS.

## 2. Schone XPU-omgeving — reeds uitgevoerd, ter reproductie

Vanuit `cmd.exe`:

```bat
cd /d C:\workspace\projects\SST-Workbench
py -3.14 -m venv .venv-a075-xpu
.venv-a075-xpu\Scripts\python.exe -m pip install --upgrade pip
.venv-a075-xpu\Scripts\python.exe -m pip install "torch==2.12.1+xpu" --index-url https://download.pytorch.org/whl/xpu
.venv-a075-xpu\Scripts\python.exe -m pip install numpy scipy pytest pybind11 reportlab
.venv-a075-xpu\Scripts\python.exe -m pip check
```

**Niet doen:** `pip install torch --index-url ...` boven op `2.12.1+cpu` en verwachten dat die automatisch wordt vervangen. Pip kan dan terecht 'Requirement already satisfied' melden. Gebruik de expliciet gepinde `+xpu`-distributie in de *nieuwe* omgeving. Verander de bestaande centrale `.venv` niet onnodig.

Verifieer:

```bat
.venv-a075-xpu\Scripts\activate.bat
python -c "import torch; print(torch.__version__,torch.version.xpu,torch.xpu.is_available(),torch.xpu.device_count())"
python -c "import torch; a=torch.ones((32,32,32),device='xpu'); b=torch.fft.fftn(a); torch.xpu.synchronize(); print(b.device,b.dtype,float(b[0,0,0].real.cpu()))"
```

Verwacht `2.12.1+xpu`, `True`, `1`, `xpu:0`, `torch.complex64`, en een nulfrequentieterm van ongeveer `32768`.

## 3. Framework 1.0.11 veilig naast 1.0.10 plaatsen

Pak `SST_Falsifier_Framework_v1.0.11_UPGRADE_PATCH.zip` uit in een tijdelijke map, bijvoorbeeld `Downloads\SST_Framework_v1.0.11_PATCH`.

```bat
cd /d C:\workspace\projects\SST-Workbench
.venv-a075-xpu\Scripts\python.exe "C:\Users\%USERNAME%\Downloads\SST_Framework_v1.0.11_PATCH\INSTALL_FRAMEWORK_V1_0_11.py" --dry-run
.venv-a075-xpu\Scripts\python.exe "C:\Users\%USERNAME%\Downloads\SST_Framework_v1.0.11_PATCH\INSTALL_FRAMEWORK_V1_0_11.py"
```

Als je het archief elders uitpakt, pas het pad aan. De installer:

- leest de aanwezige `06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10`;
- weigert om een bestaande `v1.0.11` te overschrijven;
- kopieert naar `v1.0.11` met staging + atomische publicatie;
- past alleen de nieuwe kopie aan;
- archiveert geërfde v1.0.10-`CANONICAL_FREEZE`/manifestbestanden onder `parent_v1.0.10_provenance/` zodat ze niet gelden als certificatie van v1.0.11;
- schrijft `v1.0.11_DELTA_SHA256.json`.

De upgrade wordt **DEVELOPMENT_NOT_CERTIFIED** geleverd. Lokale volledige framework-regressie en integratieruns zijn noodzakelijk voor promotie.

## 4. Een nieuwe falsifier aan v1.0.11 koppelen

Gebruik een **nieuwe niet-bevroren falsifierversie**. Wijzig geen bestanden van een bestaande `preregistration/FROZEN_PROTOCOL.json`.

In `framework_bootstrap.py` van die nieuwe instance moet de exacte pin `1.0.11` zijn (nieuw gegenereerde templates bevatten dat). Je kunt expliciet de map aanwijzen:

```bat
set "SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.11"
```

Deze omgevingsvariabele alleen is **niet** voldoende om een oude v1.0.10-bootstrap om te zetten: die weigert bewust de verkeerde versie. Genereer/migreer een afzonderlijke instance en behoud de oude freeze.

Zet in het `falsifier.toml` van een nieuwe instance:

```toml
[auto_backends]
enabled = true
require_all_devices = false
require_all_science = false
```

`enabled = true` activeert automatische beschikbaarheidstests. `require_all_devices = true` doet een expliciete strikte blokkade als een backend niet werkt; `require_all_science = true` vereist drie geobserveerde wetenschappelijke implementaties (via adapter). Zet die laatste alleen aan na implementatie en acceptatietest van de falsifier-adapter.

## 5. Automatische baseline bij iedere run

Met de nieuwe instance en de XPU-omgeving actief:

```bat
run_all.cmd BACKEND_PREFLIGHT
python -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
```

- `BACKEND_PREFLIGHT`: controleert CPU/Fourier, aanwezige C++/pybind11-module en GPU/Fourier. Geen fysische berekening.
- `FREEZE`: bevriest protocol; draait bewust geen drie fysische simulaties.
- `BASIC`/`FULL`: het bestaande `run_scientific_pipeline` blijft ongewijzigd. Daarna schrijft v1.0.11 automatisch `AUTO_BACKEND_MATRIX.json` als onderdeel van de blind-run en oproep van eventuele wetenschappelijke adapter.
- **Zonder adapter**: Python/C++/GPU worden op hardware-/softwarebeschikbaarheid onderzocht, maar wetenschappelijke records krijgen `UNIMPLEMENTED`.

Een adapter moet worden geïmplementeerd in de *nieuwe falsifier-instance* als `experiment/backend_matrix.py` met:

```python
def run_backend_matrix(*, root, cfg, mode, output_dir, devices):
    # Voer py, cpp en gpu daadwerkelijk uit met identieke beginvoorwaarden.
    # Bewaar individuele ruwe bestanden, source SHA256, precisie en numerieke verschillen.
    return {}  # vervang door echte resultaten per backend, nooit PASS simuleren
```

Dit is slechts een API-contract, niet een kant-en-klare Eulerbackend. Zie `docs/example_backend_matrix_adapter.py`.

## 6. Te controleren output

`<FalsifierNaam>_<version>-outputs/AUTO_BACKEND_MATRIX.json` bevat:

- apparaatdiagnostiek voor `py`, `cpp`, `gpu`;
- daadwerkelijke adapteruitvoering als die bestaat;
- status `UNIMPLEMENTED` / `BLOCKED` / `EXECUTED_UNQUALIFIED`;
- geen automatische wetenschappelijke `PASS`;
- precisiebeperkingen van de Arc A770 (FP32 versus CPU FP64).

`BACKEND_MANIFEST.json` bevat aanvullend een verwijzing naar dit bestand. Het framework neemt deze bestanden op in de bestaande manifesteer-/archiveringsroute, zonder oude outputroots te wissen.

## 7. Benodigde gates vóór een wetenschappelijke PASS

**A. Uitvoer:** elke backend werkelijk de fysische berekening, niet alleen een FFT-smoketest.  
**B. Precisie:** GPU-FP32-convergentie en foutbudget versus onafhankelijke CPU-FP64-referentie.  
**C. Pariteit:** identieke invoer, dezelfde fysieke eindtijd, verworpen adaptieve stappen apart registreren.  
**D. Geometrie:** dezelfde brongeometriehashes, kernparameters en randvoorwaarden.  
**E. Stabiliteit:** energie, circulatie, vorticiteit en lokale flux sluiten numeriek.  
**F. Fysische gates:** blijven falsifier-specifiek en mogen niet automatisch worden gepromoveerd.

## 8. Belangrijke beperkingen

- Een gewone `native/cpp/native.cpp` is per falsifier anders. Het framework kan geen algemene C++-wetenschappelijke kernel verzinnen.
- De framework-SYCL-worker is een **Biot–Savart**-worker en bewijst géén Fourier–Euler-uitvoering op de GPU.
- De Intel Arc A770 rapporteerde `fp64: false`; native FP64 is dus niet beschikbaar. DD32 is niet hetzelfde als IEEE FP64.
- Een tijd- en energievergelijking op verschillende backends vereist expliciet begrensde afrondingsfouten en observabele convergentie.
- De backendmatrix vervangt **niet** de domeinonafhankelijkheids- en niet-periodieke randtoetsen van A075.

## 9. Rollback

De bestaande `v1.0.10`-map is ongewijzigd. Reeds bevroren falsifiers blijven aan hun oorspronkelijke versie gepind. Gebruik die bestaande instances opnieuw om naar v1.0.10 terug te gaan; verwijder de nieuwe `v1.0.11`-map alleen nadat je hebt gecontroleerd dat nieuwe instances er niet meer naar verwijzen.

## 10. A075 zonder herschrijven van de oorspronkelijke Euler-code

Een optionele adapter voor een **nieuwe, niet-bevroren A075-versie** staat in `examples/A075_backend_matrix.py`. Die hergebruikt de bestaande functie `experiment.science.run_matrix` voor `py,cpp,gpu` en voert dus niet opnieuw een andere fysische vergelijking in.

Kopieer deze adapter alleen naar `experiment/backend_matrix.py` in de **nieuwe** A075-versie. De functie leest `A075_RUNTIME_OPTIONS_JSON`, respecteert de bestaande rekenbudgetcontrole en hergebruikt een al uitgevoerde `science/BACKEND_MATRIX.json` wanneer beschikbaar. Geen `--allow-expensive` betekent dat zware berekeningen mogen worden geblokkeerd.

**Let op:** dit is een integratievoorbeeld, geen gevalideerde volledige A075-GPU-certificering. Gebruik voor migratie het nieuwe frameworkpin- en protocolversiebeleid; wijzig geen oude `FROZEN_PROTOCOL.json`.
