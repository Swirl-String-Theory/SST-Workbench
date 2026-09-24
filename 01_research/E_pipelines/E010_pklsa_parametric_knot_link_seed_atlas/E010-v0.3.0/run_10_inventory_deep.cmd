@echo off
setlocal
if "%~1"=="" (echo Usage: %~nx0 C:\workspace\projects\SST-Workbench & exit /b 2)
call .venv\Scripts\activate.bat
python -m sst_pklsa --workbench "%~1" inventory --deep-hash --output SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs\SOURCE_INVENTORY_DEEP.json.gz
endlocal
