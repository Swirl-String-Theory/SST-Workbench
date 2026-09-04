@echo off
setlocal
set "ROOT=%~dp0"
set "VENV=%ROOT%.venv"
set "PY=%VENV%\Scripts\python.exe"
if not defined SST_KNOTS_DIR set "SST_KNOTS_DIR=C:\workspace\projects\SST-Workbench\KnotPlot\knots\final"
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=%NUMBER_OF_PROCESSORS%"
if "%SST_NATIVE_THREADS%"=="" set "SST_NATIVE_THREADS=1"
endlocal & set "ROOT=%ROOT%" & set "VENV=%VENV%" & set "PY=%PY%" & set "SST_KNOTS_DIR=%SST_KNOTS_DIR%" & set "SST_NATIVE_THREADS=%SST_NATIVE_THREADS%"
