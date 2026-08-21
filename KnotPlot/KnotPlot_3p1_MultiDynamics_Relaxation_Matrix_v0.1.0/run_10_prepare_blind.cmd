@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "_RESOLVE_INPUT.cmd" "%~1" || exit /b 1
set "PRESET=%~2"
if "%PRESET%"=="" set "PRESET=basic"
set "PYTHONPATH=%CD%\src;%CD%"
if exist blind_work rmdir /s /q blind_work
if exist private_reveal\reveal_key.json del /q private_reveal\reveal_key.json
.venv\Scripts\python.exe -m sst_phase_delay_falsifier.cli prepare --input "%INPUT%" --out blind_work --config "configs\%PRESET%.json"
exit /b %ERRORLEVEL%
