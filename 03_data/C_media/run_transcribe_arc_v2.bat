@echo off
setlocal EnableExtensions

REM ============================================================
REM SST / Intel Arc Whisper ASR launcher v2
REM ============================================================
REM Gebruik vanuit een reeds geactiveerde omgeving, bv.:
REM   call C:\Users\oscar\anaconda3\Scripts\activate.bat SSTcore_TTS
REM   cd C:\workspace\projects\SST-Workbench\media
REM   run_transcribe_arc_v2.bat
REM
REM Deze v2 vermijdt een hardcoded Conda-pad en laat OpenVINO zelf
REM de beschikbare devices kiezen. Dit voorkomt veel OpenCL/Level-Zero ruis.
REM ============================================================

echo === [A] Python omgeving ===
where python
python --version

REM Onderdruk bekende oneDNN verbose logs. De transcriptie zelf blijft zichtbaar.
set ONEDNN_VERBOSE=0
set DNNL_VERBOSE=0
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

REM Belangrijk: niet hard forceren op level_zero wanneer OpenVINO GPU via OpenCL routeert.
REM Een bestaande selector uit de shell kan OpenVINO/oneDNN verwarren, dus leegmaken.
set ONEAPI_DEVICE_SELECTOR=
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=
set ZES_ENABLE_SYSMAN=1

REM oneAPI initialisatie is optioneel. Niet fatal als het ontbreekt.
echo === [B] Optionele Intel oneAPI omgeving ===
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" >nul
  echo [OK] oneAPI setvars geladen.
) else (
  echo [Info] oneAPI setvars niet gevonden; OpenVINO runtime kan nog steeds werken via pip/driver.
)

echo === [C] OpenVINO device probe ===
python transcribe_arc_openvino_v2.py --probe-devices

echo === [D] Starten van Whisper ASR transcriptie ===
python transcribe_arc_openvino_v2.py "Rigorous_derivations_for_Swirl_String_Theory.m4a" --language nl --model openai/whisper-medium --device AUTO --out transcript_sst

if errorlevel 1 (
  echo.
  echo [Fallback] AUTO faalde. Probeer CPU zodat je in elk geval transcriptie krijgt.
  python transcribe_arc_openvino_v2.py "Rigorous_derivations_for_Swirl_String_Theory.m4a" --language nl --model openai/whisper-medium --device CPU --out transcript_sst_cpu
)

echo.
echo [Klaar] Controleer transcript_sst.txt / transcript_sst.srt.
pause