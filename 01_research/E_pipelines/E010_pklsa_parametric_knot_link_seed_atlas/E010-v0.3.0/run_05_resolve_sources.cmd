@echo off
setlocal
if "%~1"=="" (echo Usage: %~nx0 C:\workspace\projects\SST-Workbench & exit /b 2)
call .venv\Scripts\activate.bat
if not exist SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs mkdir SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs
python -m sst_pklsa --workbench "%~1" doctor --output SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs\WORKBENCH_DOCTOR.json
python -m sst_pklsa --workbench "%~1" resolve --output SST_Parametric_Knot_Link_Seed_Atlas_v0.3.0-outputs\SOURCE_RESOLUTION.json
endlocal
