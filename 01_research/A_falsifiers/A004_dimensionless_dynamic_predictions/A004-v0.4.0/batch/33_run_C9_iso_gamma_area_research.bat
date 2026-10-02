@echo off
setlocal
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
set OUT=%ROOT%\outputs\C9_iso_gamma_area_research
if not exist "%OUT%" mkdir "%OUT%"

echo Deze campagne bevat meerdere resoluties, kernels, chiraliteiten en iso-families.
choice /C JN /M "Volledige C9-researchcampagne starten"
if errorlevel 2 exit /b 0

%PY_CMD% src\sst_iso_gamma_area_clock.py campaign ^
  --config configs\C9_iso_gamma_area_research.json ^
  --output "%OUT%"
if errorlevel 1 goto :fail

%PY_CMD% tools\analyze_iso_gamma_area.py ^
  --input "%OUT%" ^
  --output "%OUT%\analysis"
if errorlevel 1 goto :fail

start "" "%OUT%\analysis"
pause
exit /b 0
:fail
echo [ERROR] C9 research campaign faalde.
pause
exit /b 1
