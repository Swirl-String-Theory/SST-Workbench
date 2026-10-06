@echo off
setlocal
cd /d "%~dp0"
set "OUT=A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs"
if "%~2"=="" (
  echo Usage: run_reveal.cmd ^<blind-summary.json^> ^<reveal-config.json^>
  exit /b 2
)
if not exist .venv (py -3 -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -q -e .
python -m a053_etptf.cli reveal --summary "%~1" --config "%~2" --output "%OUT%\reveal\REVEAL.json"
python -c "import shutil; shutil.make_archive(r'../A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs_REVEALED','zip',r'%OUT%/reveal')"
endlocal
