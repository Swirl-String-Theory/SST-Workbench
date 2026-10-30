# SST Falsifier Framework v1.1.0 — Windows-installatie en testplan

Status: DEVELOPMENT CANDIDATE, NIET Windows-hardware-gecertificeerd.
Bron: volledige v1.0.10 Canonical-bron, manifest 112/112 geverifieerd; v1.0.7 historische referentie; v1.0.11-backendintake verwerkt.

## 0 — Begrippen en veiligheidsgrenzen

- `py`: Python / NumPy binary64 (FP64, 64-bit zwevendekomma).
- `cpp`: daadwerkelijk uitgevoerde C++17-kernel via pybind11, op CPU (centrale processor).
- `gpu`: daadwerkelijk uitgevoerde GPU-kernel; Intel Arc via PyTorch XPU (Intel GPU runtime) is standaard; NVIDIA via CUDA (Compute Unified Device Architecture) is optioneel.
- **Minimaal twee van de drie CATEGORIEËN moeten wetenschappelijk hebben gedraaid.** Intel en CUDA tellen niet samen als twee categorieën; beide zijn `gpu`.
- Een `BACKEND_PREFLIGHT` (FFTs, compilecheck) telt nooit mee als wetenschappelijke uitvoering. Een BLIND ZIP/PDF kan bij mislukking diagnostisch worden gepubliceerd, maar de proces-exitcode blijft 3 en certificering is geblokkeerd.
- Een v1.1.0-instantie bevat `_sst_runtime/` met gecontroleerde sourcehashes; geen centrale installatie nodig.
- Data zelf is niet meegekopieerd: E010 blijft een externe, expliciet gepinde read-only bron.

## 1 — CPU en C++

Maak voor iedere nieuwe falsifier een omgeving, bijvoorbeeld vanuit de nieuwe versiemap:

```cmd
py -3.14 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r _sst_runtime\requirements.txt
.venv\Scripts\python.exe -m pip check
```

Installeer Visual Studio 2022 met MSVC x64 Build Tools en Windows SDK; start bij voorkeur in een x64 Developer Command Prompt. De framework-installer gebruikt lokaal `setuptools`, `pybind11` en de actuele Python Application Binary Interface (ABI; binaire programmeerinterface). Compiler- of pybind11-problemen zijn `BLOCKED`, nooit automatisch een Python-fallback.

Test:

```cmd
.venv\Scripts\python.exe -c "import numpy,pybind11,reportlab;print(numpy.__version__,pybind11.__version__)"
run_all.cmd BACKEND_PREFLIGHT
```

## 2 — Intel Arc A770 16 GiB — standaard `gpu.provider = "intel"`

Gebruik een eigen Intel-XPU-omgeving, los van CUDA. Op de doelmachine is eerder `torch==2.12.1+xpu` werkend aangetoond, maar nieuwere versies moeten onafhankelijk worden geverifieerd.

```cmd
py -3.14 -m venv .venv-intel
.venv-intel\Scripts\python.exe -m pip install --upgrade pip
.venv-intel\Scripts\python.exe -m pip install -r _sst_runtime\requirements.txt
.venv-intel\Scripts\python.exe -m pip install "torch==2.12.1+xpu" --index-url https://download.pytorch.org/whl/xpu
.venv-intel\Scripts\python.exe -c "import torch;print(torch.__version__,torch.xpu.is_available());print(torch.xpu.get_device_name(0) if torch.xpu.is_available() else 'NO XPU')"
```

Om `run_all.cmd` in die omgeving te gebruiken: activeer eerst `.venv-intel\Scripts\activate.bat` en zet `SST_PYTHON` naar de absolute `python.exe` van deze omgeving; een bestaande `.venv` wordt anders door de Windows-starter gekozen. De Intel-driver en hardware moeten XPU ondersteunen. Op de Arc A770 is native FP64 niet beschikbaar; FP32 is niet automatisch wetenschappelijk gelijkwaardig aan de CPU-FP64-referentie. DD32 (double-double op 2×FP32) blijft screening-only tenzij expliciet aangetoond.

## 3 — Optioneel NVIDIA GeForce GTX 1060 6 GiB / CUDA

De GTX 1060 is een Pascal GPU (compute capability 6.1). **CUDA 13 ondersteunt geen Pascal-targets**. Gebruik een PyTorch-uitgave met een op Pascal werkende CUDA 12.6-wheel en controleer de daadwerkelijk ondersteunde architecturen. Installeer Intel-XPU en NVIDIA-CUDA niet onbedoeld over elkaar in dezelfde omgeving.

```cmd
cd /d C:\workspace\projects\SST-Workbench
py -3.13 -m venv .venv-sst-cuda126
.venv-sst-cuda126\Scripts\python.exe -m pip install --upgrade pip
.venv-sst-cuda126\Scripts\python.exe -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu126
.venv-sst-cuda126\Scripts\python.exe -m pip install "numpy>=2,<3" scipy pytest pybind11 reportlab
.venv-sst-cuda126\Scripts\python.exe -m pip check
.venv-sst-cuda126\Scripts\python.exe -c "import torch;print(torch.__version__,torch.version.cuda,torch.cuda.is_available(),torch.cuda.get_device_name(0))"
```

Deze exacte combinatie is op de doelmachine al gecontroleerd: GeForce GTX 1060 6 GB, compute capability 6.1, PyTorch 2.7.1+cu126, NumPy 2.5.4, CUDA FFT relatieve L2-fout 3.1156637e-07. Gebruik de afzonderlijke Python 3.13-omgeving; een Windows Python 3.14-native CPython module kan niet rechtstreeks in Python 3.13 worden geladen. Een CUDA-A999-run heeft daarom alleen de Python+GPU-categorieen nodig. Beide GPU's tellen samen als een backendcategorie.

## 4 — Self-contained instanties maken

Vanuit de framework-release (alleen nodig om een NIEUWE instantie te genereren):

```cmd
python tools\new_falsifier.py A080 knot_seed_euler "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A080_knot_seed_euler\A080-v0.1.0" --profile gpu --version v0.1.0
```

Daarna werkt `A080-v0.1.0\run_all.cmd` zelfstandig, ook als de centrale frameworkmap verwijderd of hernoemd wordt. De wetenschappelijke `science_contract.json`, `source_contract.json`, `FALSIFIER_REPORT.tex`, `gate_plan.json` en `experiment/backend_matrix.py` moeten voor de nieuwe studie worden ingevuld. Zonder twee echte science-kernels blijft kwalificatie geblokkeerd.

## 5 — SST-Workbench PKLSA-Atlas (pinned read-only)

Locaties die de runtime automatisch zoekt:

```text
SST-Workbench\04_tools\A_geometry\PKLSA_Universal_Atlas_Adapter\PKLSA_Universal_Atlas_Adapter_v0.1.0\pklsa_bridge\
SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.4.0\SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip
```

Ook de reeds bestaande kortere adaptermap `PKLSA_Universal_Atlas_Adapter_v0.1.0` wordt ondersteund. Stel voor een zelfstandige, verplaatste instantie expliciet in:

```cmd
set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "E010_ATLAS=C:\workspace\projects\SST-Workbench\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas\E010-v0.4.0\SST_Parametric_Knot_Link_Seed_Atlas_v0.4.0_outputs.zip"
run_all.cmd ATLAS_VERIFY
```

De bridge controleert de E010 v0.4.0 index-hash en ZIP-digest (uit het originele v0.1.0 adaptercontract). Registreer expliciet atlas-ID's als bron vóór het wetenschappelijke FREEZE; geometrie-embeddings, knoop-topologie en bronproviders zijn verschillende identiteiten. `research_only=True` vereist expliciete opt-in. De geometrieën hebben geen automatisch bewezen meterafmetingen, Euler-evenwicht of dynamische stabiliteit.

Lees alleen een selectie met de frameworktools:

```cmd
python _sst_runtime\tools\atlas_integration.py . select --topology 3_1 --collection historical_v031 --limit 3
python _sst_runtime\tools\atlas_integration.py . export --id <EXACT_RECORD_ID> --output ..\ATLAS_CONTROL --allow-research
```

Het bestaande `pklsa_bridge.ConsumerDataset` kan daarna de create-only export met verificatie lezen. Kopieer de 1 GiB E010-atlas niet in iedere falsifier.

## 6 — Uniforme runvolgorde

```cmd
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd ATLAS_VERIFY
.venv\Scripts\python.exe -m pytest -q tests
run_all.cmd FREEZE
run_all.cmd BASIC
run_all.cmd FULL
run_all.cmd CERTIFY
```

Voor een echte studie gelden extra preregistratie-, convergentie- en provenancecontroles. Een `FULL`/`CERTIFY` run die minder dan twee echte backends documenteert, publiceert wel een auditbaar diagnostisch rapport en ZIP, maar eindigt met exitcode 3. Een beschadigde runtime-snapshot wordt al bij bootstrap geweigerd.

### Vereiste artefacten

- `<name>_<version>-outputs/`: unieke `RUN_ID`, gates, bron-, backend-, science-evidence- en outputmanifesten; `AUTO_BACKEND_MATRIX.json` en `REPORT_RENDER_BLIND.json`.
- In de bovenliggende directory unieke `_BLIND.zip`, bij reveal apart `_REVEALED.zip`, PDF, ZIP SHA-256 sidecar.
- Indien LaTeX niet werkt: expliciet `DEGRADED_DIAGNOSTIC_ONLY` ReportLab-PDF; certificering blijft geblokkeerd. Installeer MiKTeX/TeX Live en gebruik `REPORT_ONLY` om de volledige wetenschappelijke PDF alsnog te publiceren zonder bestaande resultaten te wijzigen.

## 7 — Blinde/reveal-koppeling en scope

Geen automatische fysische PASS. Een `EXECUTION_CONTRACT_PASS` bevestigt slechts dat twee onderscheiden kernels invoer, uitvoer en hashes hebben geregistreerd. De onafhankelijkheid van wiskundige implementaties, nauwkeurigheid, spatial/temporal convergence, finite-core gedrag, brononafhankelijkheid en alle preregistratie-gates blijven afzonderlijk verplicht. De 3-providers zijn technische uitvoeringscategorieën, niet drie onafhankelijke empirische datasets.

## Referenties

- PyTorch, *Get Started Locally*: https://pytorch.org/get-started/locally/
- PyTorch, *Getting Started on Intel GPU*: https://docs.pytorch.org/get-started/additional-platforms/
- PyTorch Team (2026), *PyTorch 2.12 Release Blog*: https://pytorch.org/blog/pytorch-2-12-release-blog/
- NVIDIA (2025), *CUDA Toolkit 13.0 Release Notes*: https://docs.nvidia.com/cuda/archive/13.0.0/cuda-toolkit-release-notes/

## 8 — A999 E010 integration control / release-acceptatie (RC1)

Dit is een extra *numerieke integratiefalsifier*, geen fysische SST-falsifier. Gebruik de
reeds door de gebruiker geverifieerde historische E010-export van exact een trefoil-record.
De E010-atlas zelf blijft read-only. Het nieuwe A999-experiment kopieert alleen de
kleine *geverifieerde selectie* naar zijn eigen `input/e010_export/`; daardoor is de
scientific input ook lokaal portable. De externe PKLSA adapter v0.1.0 blijft voor
hash-gecontroleerde herinname nodig. Een latere echte wetenschapstest is een apart project.

In `cmd.exe`, vanuit de framework-releasemap:

```bat
set "WB=C:\workspace\projects\SST-Workbench"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.1.0_RC1"
set "PYX=%WB%\.venv-a075-xpu\Scripts\python.exe"
set "DATASET=C:\Users\oscar\AppData\Local\Temp\SST_A999_E010_trefoil_18736"
set "A999=%TEMP%\A999_E010_RC1_%RANDOM%"
set "SST_WORKBENCH_ROOT=%WB%"
set "SST_PYTHON=%PYX%"
cd /d "%FW%"
"%PYX%" tools\prepare_a999_e010.py --dataset "%DATASET%" --output "%A999%" --record CAR_0081c5a310c30e50 --gpu intel
cd /d "%A999%"
run_all.cmd BACKEND_PREFLIGHT
run_all.cmd FREEZE
run_all.cmd FULL
"%PYX%" "%FW%\tools\verify_a999_release.py" --instance "%A999%" --output "%TEMP%\A999_RC1_ACCEPTANCE_%RANDOM%.json"
```

De `DATASET`-waarde is het pad uit de eerdere feitelijke Windows-export.
Als dat tijdelijke pad is verwijderd, voer de E010-export opnieuw uit en pas
`DATASET` aan. `prepare_a999_e010.py` weigert bestaande doelen. De native C++
module moet opnieuw worden gebouwd in dezelfde Python Application Binary
Interface-omgeving; Intel XPU wordt zonder GPU-wissel gebruikt.

**Releasecriterium:** `FULL` exit 0; `verify_a999_release.py` exit 0 met
`status=PASS_TECHNICAL_INTEGRATION_ONLY`; G0/G1/G2/G10 zijn PASS en G10
heeft kwalificatie `QUALIFIED`; PDF renderer is echt LaTeX `PASS` (niet
`DEGRADED_DIAGNOSTIC_ONLY`); bron-, evidence-, output- en ZIP-hashes kloppen.
Een technische PASS betekent geen Euler- of trefoil-stabiliteitsresultaat.

NVIDIA CUDA kan apart gecontroleerd worden met dezelfde export, maar een
*nieuwe* A999-instantie en `--gpu cuda`, uitgevoerd met `SST_PYTHON` naar
`.venv-sst-cuda126\Scripts\python.exe`. Dit is optioneel; Intel blijft de
standaard. Forceer geen oud CPP cp314-binary in Python cp313.

De centrale release is tot deze daadwerkelijke Windows `FULL`-acceptatie een
**RELEASE CANDIDATE**. Bestaande bevroren instanties en oudere Canonical-versies
mogen nooit in-place worden vervangen. Na een echte Windows PASS kan de
nieuwe, ongewijzigde releasehash via een afzonderlijk certificeringsrecord
worden gepromoveerd; geen retrospectieve zelf-certificering.

## 9 — Installatiebeleid zonder overschrijven

Het RC1 archief heeft een eigen map `SST_Falsifier_Framework_v1.1.0_RC1`.
Pak die uit in `06_templates/SST_Falsifier_Framework/` maar **niet** bovenop
`SST_Falsifier_Framework_v1.1.0` of een Canonical 1.0.x-bron. Vervang niet
zelf de bevroren runtime van bestaande falsifiers. Promotie na lokale
acceptatie is een aparte, gehashte releasebeslissing.
