@echo off
setlocal
cd /d "%~dp0"
set "WB=%~1"
set "OUT=A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
if not exist .venv (py -3 -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -q -e .
python -m a053_etptf.cli plan --workbench-root "%WB%" --output "%OUT%\WORKBENCH_PLAN.json"
endlocal
