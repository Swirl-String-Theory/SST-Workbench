@echo off
setlocal
cd /d "%~dp0"
set PRESET=%1
if "%PRESET%"=="" set PRESET=basic
.venv\Scripts\python.exe -m a056_falsifier.pipeline --input data\synthetic_blind --config configs\%PRESET%.json || exit /b 1
