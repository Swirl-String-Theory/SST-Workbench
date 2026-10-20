@echo off
setlocal
set "ADAPTER_ROOT=%~dp0"
set "ATLAS_ROOT=%ADAPTER_ROOT%..\A003-v0.1.1"
if defined SST_ATLAS_ROOT set "ATLAS_ROOT=%SST_ATLAS_ROOT%"
if not "%~1"=="" set "ATLAS_ROOT=%~1"
if not exist "%ATLAS_ROOT%\manifest.json" (
  echo FAIL_CLOSED: Atlas ontbreekt: "%ATLAS_ROOT%\manifest.json" 1>&2
  exit /b 2
)
set "SST_ATLAS_ROOT=%ATLAS_ROOT%"
python "%ADAPTER_ROOT%fourier_atlas_adapter.py" --atlas "%ATLAS_ROOT%" --out "%ADAPTER_ROOT%outputs" catalog
if errorlevel 1 exit /b 1
python -m unittest discover -s "%ADAPTER_ROOT%tests" -v
if errorlevel 1 exit /b 1
echo GEOMETRIC_IMPORT_QUALIFIED - no physics/topology certification asserted
exit /b 0
