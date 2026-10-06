@echo off
setlocal
cd /d "%~dp0"
set "OUT=A053_Electron_Topological_Phase_Transition_Tournament_v0.1.0-outputs"
if not exist .venv (py -3 -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install -q --upgrade pip
python -m pip install -q -e . -r requirements.txt
pytest -q
if errorlevel 1 exit /b %errorlevel%
python -m a053_etptf.cli selftest --config configs\basic.json --output-dir "%OUT%\instrument_selftest"
endlocal
