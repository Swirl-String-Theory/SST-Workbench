@echo off
setlocal
cd /d "%~dp0"
set "INPUT=%~1"
set "OUT=%~2"
if "%INPUT%"=="" (set "IARG=") else (set "IARG=--input "%INPUT%"")
if "%OUT%"=="" (set "OARG=") else (set "OARG=--out "%OUT%"")
".venv\Scripts\python.exe" -m einstein_sst_gates.cli measure --config config\normal.json %IARG% %OARG%
