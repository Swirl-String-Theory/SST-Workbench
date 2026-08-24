@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
set "MODE=%~3"
if "%MODE%"=="" set "MODE=confirmatory"
if not exist ".venv\Scripts\python.exe" ( echo ERROR: run run_00_install.cmd first. & exit /b 5 )
if not exist "build" mkdir "build" >nul 2>nul
if exist "build\resolved_input.txt" del /q "build\resolved_input.txt" >nul 2>nul
".venv\Scripts\python.exe" resolve_input.py --explicit "%~1" --repo-dir "%CD%" --pattern "*_i10000.txt" --out-file "%CD%\build\resolved_input.txt"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" exit /b %RC%
set "INPUT="
for /f "usebackq delims=" %%I in ("build\resolved_input.txt") do if not defined INPUT set "INPUT=%%I"
if not defined INPUT ( echo ERROR: resolved input path is empty. & exit /b 4 )
set "PYTHONPATH=%CD%\src;%CD%"
if exist blind_work rmdir /s /q blind_work
if exist private_reveal\reveal_key.json del /q private_reveal\reveal_key.json
if exist results rmdir /s /q results
mkdir results >nul 2>nul
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli prepare --input "%INPUT%" --out blind_work --config "configs\%PRESET%.json" --mode "%MODE%"
exit /b %ERRORLEVEL%
