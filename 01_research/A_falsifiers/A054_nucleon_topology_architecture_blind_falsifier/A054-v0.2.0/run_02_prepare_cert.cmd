@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (echo Usage: run_02_prepare_cert.cmd ^<SST-Workbench-root^> ^<output-dir^> [preset] & exit /b 2)
if "%~2"=="" (echo Missing output-dir & exit /b 2)
set "PRESET=%~3"
if "%PRESET%"=="" set "PRESET=basic"
if /I "%PRESET%"=="basic" (set N=72) else if /I "%PRESET%"=="extended" (set N=96) else (set N=112)
python -m a054_ntaf.cli prepare-cert --workbench "%~1" --output "%~2" --preset "%PRESET%" --n %N%
exit /b %errorlevel%
