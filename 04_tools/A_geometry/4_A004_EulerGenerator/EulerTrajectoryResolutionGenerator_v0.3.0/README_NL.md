# Euler Trajectory Resolution Generator v0.3.0 — Intel Arc XPU

**Status: DEVELOPMENT / GPU FP32 screening only.** Nieuwe, zelfstandige generator, geen wijziging van bestaande A075/A077-falsifiers. De volledige originele Framework v1.1.0-runtime en de instance-template zijn aanwezig onder `_sst_runtime/`, met onveranderde hash-inventaris (142/142). Er is **geen** officiële Framework FREEZE/CERTIFY uitgevoerd voor deze aparte tool.

## Wat is echt geïmplementeerd?

- **GPU-evolutie**: 3D getrunceerde incompressibele Euler-vergelijking `du/dt = P(u x curl(u))`, complexe `torch.complex64` FFT, Leray-projectie, RK4 en trilineaire periodieke tracerinterpolatie, geheel op dezelfde PyTorch `xpu:0`-device.
- **DD32 dubbel-single voor tracerposities**: per coördinaat twee `float32`-getallen, met foutgecompenseerde optelling tijdens de trajectintegratie. Dit voorkomt verlies van kleine verplaatsingen in lange trajecten. **Belangrijk: de FFT, de Euler-RHS, de snelheidsinterpolatie en de RK4-veldstadia blijven FP32.** Het is dus *geen volledige DD32-Euleroplosser*.
- **Officiële Framework-DD32-referentie**: `framework_preflight.cmd` verifieert 142 bestanden en controleert DD32-scalarrekenkunde. `run_dd32_sycl_smoke.cmd` start de echte oneAPI/SYCL-DD32 Biot–Savart-smoke uit het ongewijzigde Framework wanneer `icpx` en de Intel-driver zijn geïnstalleerd. Dit is geen Euler-DD32-certificering.
- **Beide providers**: hash-geverifieerde A075-v0.2.10 (`experiment/euler3d.py` plus Ruban-bestand) en A077-v0.1.2 (`science/euler_field.py`). De Python-bron maakt de initiële 3D Euler-toestand eenmalig aan op de CPU, daarna worden alle 3D evolutie- en interpolatietensors op de GPU berekend. Voor deze initialisatie blijft host-RAM nodig.
- **Vijf onderzoeksassen**: spatiaal, temporeel, kernbreedte, boxgrootte, perturbaties via `run_gpu_studies.cmd`. Planning zonder `--execute`; iedere run schrijft een nieuw archief met SHA-256.
- **Fail-closed**: geen automatische CPU-fallback, GPU-VRAM- en host-RAM-preflight, CFL-limiet, bronhashcontroles, niet-finite-controles, geen valse 2-van-3-backendclaims.

## Windows-installatie

1. Pak het bronarchief uit als aparte map naast de falsifiers, bijvoorbeeld `C:\workspace\projects\SST-Workbench\04_tools\EulerTrajectoryResolutionGenerator_v0.3.0\`. De laatste map is een voorbeeld, geen voorgeschreven catalogus-ID.
2. Gebruik **de bestaande XPU-geschikte PyTorch-installatie** (`torch.xpu.is_available()` moet `True` geven). Gebruik **niet** zomaar `pip install torch` wanneer dit je `+xpu`-build zou overschrijven.
3. In een opdrachtprompt vanuit de generator:

```bat
python -m pip install numpy scipy pytest
python -c "import torch; print(torch.__version__); print('Arc XPU:', torch.xpu.is_available())"
python framework_preflight.py
python -m pytest -q tests
```

### GPU-CMD’s en venv-selectie

`run_gpu_studies.cmd` en `framework_preflight.cmd` kiezen automatisch de interpreter via `set_sst_python.cmd`:

1. Bestaande omgevingsvariabele `SST_PYTHON` (wint altijd).
2. Anders lokale `.env` in deze map (`SST_PYTHON`, `SST_GPU_LANE`, optioneel `SST_WORKBENCH_ROOT`).
3. Anders default lane **`xpu`** → workbench-root `.venv-a075-xpu\Scripts\python.exe`.
4. Lane `cuda` → `.venv-sst-cuda126\Scripts\python.exe`.

Kopieer `.env.example` naar `.env` om te overriden. Ontbreekt het gekozen `python.exe`, dan stoppen de GPU-CMD’s met een fout (geen stille fallback naar systeem-Python).

Gebruik exact de werkelijke paden naar je A075- en A077-bronmappen.

### Eerste echte A077-GPU-run

```bat
run_gpu.cmd --provider a077 --source "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.2" --grid 64 --time 0.02 --dt 0.002 --markers 16 --precision dd32-tracer --vram-limit-gib 12 --ram-limit-gib 16 --execute
```

### Eerste echte A075-GPU-run

```bat
run_gpu.cmd --provider a075 --source "C:\WERKELIJK_PAD\A075-v0.2.10" --grid 64 --time 0.02 --dt 0.002 --markers 16 --precision dd32-tracer --vram-limit-gib 12 --ram-limit-gib 16 --execute
```

### Studieplanner; géén berekeningen totdat --execute expliciet is opgegeven

```bat
run_gpu_studies.cmd --a075-root "C:\WERKELIJK_PAD\A075-v0.2.10" --a077-root "C:\workspace\projects\SST-Workbench\01_research\A_falsifiers\A077_Electron_Layer_Leapfrogging\A077-v0.1.2" --profile pilot --studies all --memory-limit-gib 12 --ram-limit-gib 16
```

Voeg na beoordeling van het plan `--execute --skip-unaffordable` toe. `--skip-unaffordable` maakt een onvolledige campagne, geen PASS.

### Framework DD32 SYCL-rooktest (afzonderlijke Biot–Savart-kernel)

```bat
run_dd32_sycl_smoke.cmd
```

Vereist Intel oneAPI DPC++ en geschikte GPU-drivers. Dit commando test de **originele** SYCL-worker, niet de GPU-Euler-FFT.

## RAM/VRAM realiteit

De Arc A770 heeft 16 GB GDDR6 volgens Intel; praktisch reserveert de planner 25% plus een strikte gebruikerslimiet van standaard 12 GiB. Conservatieve planningsformule:

\[B_{\rm GPU}^{\rm budget}(N)=1.35\times 960 N^3\;\mathrm{bytes}.\]

Dit is **geen gemeten piek**, en de werkelijk benodigde FFT-workspaces/drivers kunnen daarvan afwijken; daarom is een eerste korte XPU-run noodzakelijk. Voor de CPU-bronconstructie geldt nog een afzonderlijke conservatieve begroting `1.5 GiB + 384*N**3 bytes`. Geen van beide controles mag worden genegeerd. De pilot gebruikt bewust **eigen CPU-initiële gegevens**, zodat bronprovenance niet verandert.

| N | Gebudgetteerd videogeheugen (GiB) | Default 12-GiB-guard |
|---:|---:|---|
| 64 | 0.32 | plannings-PASS |
| 96 | 1.07 | plannings-PASS |
| 128 | 2.53 | plannings-PASS |
| 170 | 5.93 | plannings-PASS |
| 192 | 8.54 | plannings-PASS |
| 204 | 10.25 | plannings-PASS |
| 238 | 16.27 | geweigerd |
| 260 | 21.21 | geweigerd |
| 390 | 71.60 | geweigerd |

Voor A077 is nominale geometrische kernresolutie van 4 cellen bij ~170³ bereikbaar binnen **het geschatte GPU-budget**; voor A075 (77/500 minor radius) vraagt die ~260³, buiten het conservatieve budget. Vier *spectraal behouden* cellen vergen weer hogere roosters. Een volledige fysische kernstabiliteitskwalificatie vereist een nieuw low-storage of gedistribueerd algoritme en onafhankelijke resolutie-, tijdstap-, kernbreedte-, box- en perturbatieconvergentie; hogere N alleen is niet genoeg.

## Wetenschappelijke gates

- TG0: Framework runtime-integriteit; TG1: gepinde bronherkomst.
- TG2: werkelijk uitgevoerde XPU FP32 solver-screening (alleen `xpu`, nooit CPU-test).
- TG3: volledige GPU-DD32 Euler/FFT **UNRESOLVED**; TG4: onafhankelijk Euler-pariteitonderzoek **UNRESOLVED**.
- TG5: materiële kernstabiliteit, topo-/helixdynamica en spin-½ **UNRESOLVED**.

De GPU-export bevat `RUN_MANIFEST.json`, `FRAMEWORK_DIAGNOSTIC_GATE_LEDGER.json`, `GPU_BACKEND_EVIDENCE.json`, `trial_XXXX/trajectory.npz`, `conservation.csv`, diagnostiek, `OUTPUT_MANIFEST.json`, ZIP en ZIP.sha256. De original Framework-runner wordt **niet** ten onrechte aangeroepen alsof dit reeds een geregistreerde twee-backendfalsifier is.

## Reproduceerbaarheid en bronnen

Zie `docs/COMPATIBILITY_AUDIT_NL.md` (overgenomen van v0.2.0, adapterstatus blijft ongewijzigd). Werkelijke XPU-run en Windows GPU-FFT-pariteit zijn op de ontwikkelhost **niet** uitgevoerd: die beschikt over PyTorch CPU-only. CPU-tests controleren code- en gegevensintegratie, geen XPU-stabiliteit of prestatiewinst.

Literatuur voor de overgenomen niet-originele methoden:

```latex
\begin{thebibliography}{9}
\bibitem{Saffman1992} P. G. Saffman (1992), \emph{Vortex Dynamics}, Cambridge University Press, doi:10.1017/CBO9780511624063.
\bibitem{HouLi2007} T. Y. Hou and R. Li (2007), ``Computing nearly singular solutions using pseudo-spectral methods,'' \emph{Journal of Computational Physics} 226, 379--397, doi:10.1016/j.jcp.2007.04.015.
\bibitem{Dekker1971} T. J. Dekker (1971), ``A Floating-Point Technique for Extending the Available Precision,'' \emph{Numerische Mathematik} 18, 224--242, doi:10.1007/BF01397083.
\bibitem{DaGracaDefour2006} G. Da Gra\c{c}a and D. Defour (2006), ``Implementation of float-float operators on graphics hardware,'' arXiv:cs/0603115, https://arxiv.org/abs/cs/0603115.
\end{thebibliography}
```
