@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=py -3"

%PY% repair_a054_r2_provenance.py --verify-only
