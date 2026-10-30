@echo off
setlocal
cd /d "%~dp0"
set "MODE=%~1"
if "%MODE%"=="" set "MODE=SMOKE"
if /I "%MODE%"=="FREEZE" goto NOFRAMEWORK
if /I "%MODE%"=="CERTIFY" goto NOFRAMEWORK
if /I "%MODE%"=="REVEAL" goto NOFRAMEWORK
if /I "%MODE%"=="TEST" (
    py -m pytest -q tests
    exit /b %errorlevel%
)
py -m pytest -q tests
if errorlevel 1 exit /b 1
if /I "%MODE%"=="CONVERGE" (
    py -m ruban_falsifier.convergence
    exit /b %errorlevel%
)
py -m ruban_falsifier %MODE%
exit /b %errorlevel%
:NOFRAMEWORK
echo REFUSED: Framework v1.1 runtime not installed and integrity-validated.
exit /b 4
