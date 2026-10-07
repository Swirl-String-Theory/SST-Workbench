@echo off
setlocal
cd /d "%~dp0"
set "WB=%~1"
if "%WB%"=="" if defined SST_WORKBENCH_ROOT set "WB=%SST_WORKBENCH_ROOT%"
if "%WB%"=="" set "WB=C:\workspace\projects\SST-Workbench"
if not exist "%WB%" (echo [ERROR] SST-Workbench root not found: %WB% & exit /b 2)
if "%~2"=="" (echo Missing output-dir & exit /b 2)
set "PY=%CD%\.venv\Scripts\python.exe"
if not exist "%PY%" (echo [ERROR] Missing .venv. Run run_00_install.cmd first. & exit /b 2)
set "PRESET=%~3"
if "%PRESET%"=="" set "PRESET=basic"
if /I "%PRESET%"=="basic" (set N=72) else if /I "%PRESET%"=="extended" (set N=96) else (set N=112)
"%PY%" -m a054_ntaf.cli prepare-cert --workbench "%WB%" --output "%~2" --preset "%PRESET%" --n %N%
exit /b %errorlevel%
