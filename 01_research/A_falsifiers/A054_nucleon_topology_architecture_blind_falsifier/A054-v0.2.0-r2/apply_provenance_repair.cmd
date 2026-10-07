@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem This script is intended to be copied into:
rem   A054_nucleon_topology_architecture_blind_falsifier\A054-v0.2.0-r2
rem or run with that directory as the current working directory.

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  where py >NUL 2>NUL
  if errorlevel 1 (
    echo ERROR: neither .venv\Scripts\python.exe nor py.exe was found.
    exit /b 2
  )
  set "PY=py -3"
)

%PY% repair_a054_r2_provenance.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo Provenance repair PASS.
echo You can now run verify_provenance_repair.cmd and then restart A055 v0.3.0.
