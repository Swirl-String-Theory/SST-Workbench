# SST Falsifier Framework v1.1.1 — DD32-standaard (DEVELOPMENT)

**NIET CANONICAL_FROZEN.** De bestaande v1.1.0 blijft ongewijzigd en is de laatst bewezen Canonical-versie. Dit pakket is een ontwikkelkandidaat voor DD32 op Intel Arc en NVIDIA CUDA. De CUDA-kernel is nog niet op de GTX 1060 gebouwd of uitgevoerd; niet als geslaagd rapporteren.

## Veranderde standaard

Nieuwe self-contained falsifiers krijgen in `falsifier.toml`:

```toml
[gpu]
provider = "intel"
precision = "dd32"
```

`provider = "cuda"` kiest de afzonderlijke CUDA-route, eveneens met DD32. De frameworkgate weigert `float32`-bewijsmateriaal wanneer DD32 gevraagd is en vergelijkt de gehashte binaire worker met het daadwerkelijke uitvoeringbewijs. **Geen stilzwijgende FP32-fallback.** DD32 blijft een numerieke screeningsroute, geen formele FP64-vervanger. De minimale 2-uit-3-backendregel blijft gehandhaafd.

- Python: NumPy FP64 referentie.
- C++: pybind11 FP64, native module.
- Intel Arc A770: externe SYCL-worker met DD32 (FP32x2); geen `torch.float32` in de wetenschappelijke A999-kernel.
- NVIDIA GTX 1060: externe CUDA-worker met DD32, gebouwd met `nvcc` 12.x voor `sm_61`; geen PyTorch-FP32-fallback.

## Vereisten Windows

Voor Intel: de bestaande Python 3.14 / Intel-XPU-omgeving met `numpy`, `pytest`, `pybind11`, `reportlab`; Intel oneAPI `icpx`, en MSVC x64 linkeromgeving. Gebruik je bestaande goedgekeurde oneAPI-installatie, niet automatisch een nieuwe.

Voor NVIDIA: de bestaande Python 3.13 CUDA 12.6-omgeving met `numpy`, `pytest`, `pybind11`, `reportlab`; CUDA Toolkit 12.6 `nvcc` en Visual Studio 2022 MSVC x64 Build Tools. PyTorch CUDA mag aanwezig zijn maar is **niet** de DD32-kernel. `SST_CUDA_ARCH` staat standaard op `sm_61`. Wijzig die alleen als je een andere kaart gebruikt en leg de archwaarde vast. CUDA 13.x is geen doel van deze Pascal-route.

## A999-integratietest: Intel

Pak de ontwikkel-ZIP uit naast v1.1.0. Open `cmd.exe`:

```bat
set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
set "SST_PYTHON=%WB%\.venv-a075-xpu\Scripts\python.exe"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.1.1_DD32_DEVELOPMENT"
cd /d "%FW%"
tools\run_a999_dd32_validation.cmd "%TEMP%\SST_A999_E010_trefoil_18736" intel
```

## A999-integratietest: NVIDIA GTX 1060

Open een **nieuw** `cmd.exe`, zodat de Intel-omgeving niet met de CUDA-omgeving wordt gemengd:

```bat
set "WB=C:\workspace\projects\SST-Workbench"
set "SST_WORKBENCH_ROOT=%WB%"
set "SST_PYTHON=%WB%\.venv-sst-cuda126\Scripts\python.exe"
set "SST_CUDA_ARCH=sm_61"
set "FW=%WB%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.1.1_DD32_DEVELOPMENT"
cd /d "%FW%"
nvcc --version
tools\run_a999_dd32_validation.cmd "%TEMP%\SST_A999_E010_trefoil_18736" cuda
```

Bij een compilerfout verandert het framework niets aan v1.1.0 en zal geen gefingeerde GPU-berekening rapporteren. Indien `nvcc` het MSVC-toolset niet ondersteunt, los dit eerst in een afzonderlijke toolchainomgeving op; gebruik niet zonder beoordeling `-allow-unsupported-compiler`.

**Let op:** Een succesvolle `run_all.cmd FULL` kan zelfs bij uitgeschakelde GPU op Python+C++ voldoen aan de algemene 2-uit-3-regel. Controleer daarom daarnaast expliciet:

1. `AUTO_BACKEND_MATRIX.json`: `scientific.gpu.scientific_execution == true`.
2. `scientific.gpu.precision == "dd32-fp32x2"`.
3. `scientific.gpu.actual_backend == "sycl-native-dd32"` (Intel) of `"cuda-native-dd32"` (NVIDIA).
4. Gehashte workerbinary en bron; verifieer `compiled_binary_sha256` en `gpu_worker_build_fingerprint_sha256`.
5. De G10-numerieke foutgrens is maximaal `1e-8` voor deze DD32-controle; op hardware moet de werkelijke uitkomst worden afgelezen.

## Wetenschappelijke status

Een geslaagde A999-test bewijst uitvoerings- en numerieke integratie voor één regulier Biot–Savart-kernprobleem, niet een Euler-evenwicht, tijdsevolutie, finite-core-convergentie of stabiliteit van een knoop. Nieuwe falsifiers moeten zelf ruimtelijke, temporele en fysische gates afleiden en preregistreren. DD32 heeft geen automatisch recht op dezelfde nauwkeurigheid als IEEE FP64, en prestaties op Intel Arc / GTX 1060 zijn niet vooraf bewezen.
