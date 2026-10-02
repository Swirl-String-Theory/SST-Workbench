@echo off
setlocal
if "%~2"=="" (echo Usage: %~nx0 WORKBENCH_ROOT PKLSA_V020_ROOT_OR_ZIP [TOPOLOGY] & exit /b 2)
set TOPO=%~3
if "%TOPO%"=="" set TOPO=3_1
call .venv\Scripts\activate.bat
python -m sst_pklsa --workbench "%~1" qualify --base "%~2" --topology "%TOPO%" --config configs\qualification_basic.json --out SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs\qualification\%TOPO%
endlocal
