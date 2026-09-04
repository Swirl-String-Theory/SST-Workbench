@echo off
setlocal

echo === [A] Activeren van Conda Omgeving ===
call C:\Users\oscar\anaconda3\Scripts\activate.bat SSTcore_TTS

echo === [B] Intel oneAPI / Level Zero omgeving ===
if exist "C:\Program Files (x86)\Intel\oneAPI\setvars.bat" (
  call "C:\Program Files (x86)\Intel\oneAPI\setvars.bat"
)

:: Selecteer uitsluitend de discrete Intel Arc GPU wanneer level_zero:0 jouw Arc kaart is.
:: Controleer dit bij twijfel met list_devices.cpp of met OpenVINO device query.
set ONEAPI_DEVICE_SELECTOR=level_zero:0
set SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
set ZES_ENABLE_SYSMAN=1

echo === [C] Starten van Whisper ASR transcriptie op Arc/OpenVINO ===
python transcribe_arc_openvino.py "Rigorous_derivations_for_Swirl_String_Theory.m4a" --language nl --model openai/whisper-medium --device GPU --out transcript_sst

pause