@echo off
setlocal
if "%~2"=="" (
  echo Usage: %~nx0 C:\workspace\projects\SST-Workbench C:\path\SST_Parametric_Knot_Link_Seed_Atlas_v0.2.0.zip [TOPOLOGY]
  exit /b 2
)
call run_00_setup.cmd || exit /b 1
call run_05_resolve_sources.cmd "%~1" || exit /b 1
call run_10_inventory.cmd "%~1" || exit /b 1
set TOPO=%~3
if "%TOPO%"=="" set TOPO=3_1
call .venv\Scripts\activate.bat
python -m sst_pklsa --workbench "%~1" qualify --base "%~2" --topology "%TOPO%" --config configs\qualification_extended.json --out SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs\qualification\%TOPO% || exit /b 1
call run_90_pack.cmd || exit /b 1
endlocal
