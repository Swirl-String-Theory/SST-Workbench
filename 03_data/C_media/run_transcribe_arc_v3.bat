@echo off
setlocal EnableExtensions

REM ============================================================
REM SST / Intel Arc Whisper ASR launcher v3
REM ============================================================
REM Gebruik:
REM   run_transcribe_arc_v3.bat "mijn_audio.m4a"
REM
REM Output automatisch:
REM   mijn_audio_transcript.txt
REM   mijn_audio_transcript.srt
REM
REM Vereist: actieve Python/Conda omgeving met requirements geinstalleerd.
REM Voorbeeld:
REM   call C:\Users\oscar\anaconda3\Scripts\activate.bat SSTcore_TTS
REM   cd C:\workspace\projects\SST-Workbench\media
REM   run_transcribe_arc_v3.bat "De_logische_fundamenten_van_Swirl-String_Theory.m4a"
REM ============================================================

if "%~1"=="" (
  echo [Gebruik] run_transcribe_arc_v3.bat "audiofile.m4a"
  echo.
  echo Voorbeeld:
  echo   run_transcribe_arc_v3.bat "De_logische_fundamenten_van_Swirl-String_Theory.m4a"
  exit /b 2
)

set "AUDIO_IN=%~1"
if not exist "%AUDIO_IN%" (
  echo [Fout] Audiofile niet gevonden: "%AUDIO_IN%"
  exit /b 2
)

REM Outputnaam wordt door Python automatisch gemaakt:
REM   %%~n1_transcript.txt en %%~n1_transcript.srt
set "OUT_TXT=%~dpn1_transcript.txt"
set "OUT_SRT=%~dpn1_transcript.srt"

echo === [A] Python omgeving ===
where python
python --version

REM Onderdruk bekende oneDNN verbose logs. De transcriptie zelf blijft zichtbaar.
set ONEDNN_VERBOSE=0
set DNNL_VERBOSE=0
set HF_HUB_DISABLE_SYMLINKS_WARNING=1

REM Niet hard forceren op Level-Zero; laat OpenVINO AUTO kiezen.
set ONEAPI_DEVICE_SELECTOR=
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=
set ZES_ENABLE_SYSMAN=1

echo === [B] Optionele Intel oneAPI omgeving ===
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" >nul
  echo [OK] oneAPI setvars geladen.
) else (
  echo [Info] oneAPI setvars niet gevonden; OpenVINO runtime kan nog steeds werken via pip/driver.
)

echo === [C] OpenVINO device probe ===
python transcribe_arc_openvino_v3.py --probe-devices

echo === [D] Starten van Whisper ASR transcriptie ===
echo [Audio] "%AUDIO_IN%"
echo [Output] "%OUT_TXT%"
python transcribe_arc_openvino_v3.py "%AUDIO_IN%" --language nl --model openai/whisper-medium --device AUTO

if errorlevel 1 (
  echo.
  echo [Fallback] AUTO faalde. Probeer CPU zodat je in elk geval transcriptie krijgt.
  python transcribe_arc_openvino_v3.py "%AUDIO_IN%" --language nl --model openai/whisper-medium --device CPU
)

if exist "%OUT_TXT%" (
  echo.
  echo [Klaar] Transcript gemaakt:
  echo   "%OUT_TXT%"
  if exist "%OUT_SRT%" echo   "%OUT_SRT%"
) else (
  echo.
  echo [Waarschuwing] Geen TXT gevonden op verwacht pad: "%OUT_TXT%"
  echo Controleer de terminal-output hierboven voor de exacte [I/O] Transcript TXT regel.
)

pause
