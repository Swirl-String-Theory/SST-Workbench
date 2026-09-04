@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe py -3 -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m katlas_source.cli --config config.json fetch-profile sst_curated %* || exit /b 1
