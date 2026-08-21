@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (set OUTDIR=outputs_blind) else (set OUTDIR=%~1)
call .venv\Scripts\activate.bat
python -m sst_v_arrow_falsifier unblind "%OUTDIR%" --target sealed\unblind_target.json --config config\default.json
endlocal
