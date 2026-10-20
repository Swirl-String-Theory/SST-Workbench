@echo off
setlocal
set "ADAPTER_ROOT=%~dp0"
set "ATLAS_ROOT=%ADAPTER_ROOT%..\..\SST_Fourier_Knot_Seed_Atlas\v0.1.1"
if not "%~1"=="" set "ATLAS_ROOT=%~1"
set "SST_ATLAS_ROOT=%ATLAS_ROOT%"
python "%ADAPTER_ROOT%fourier_atlas_adapter.py" --atlas "%ATLAS_ROOT%" --out "%ADAPTER_ROOT%outputs" catalog
if errorlevel 1 exit /b 1
python -m unittest discover -s "%ADAPTER_ROOT%tests" -v
if errorlevel 1 exit /b 1
echo GEOMETRIC_IMPORT_QUALIFIED - no physics/topology certification asserted
