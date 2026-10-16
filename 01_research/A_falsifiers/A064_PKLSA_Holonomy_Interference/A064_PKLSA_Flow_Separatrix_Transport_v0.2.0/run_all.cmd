@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
    py -3 -m venv .venv
    if errorlevel 1 exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 exit /b 1
if "%~1"=="" goto euler_default
if /I "%~1"=="SELFTEST" goto tests
if /I "%~1"=="REPORT" goto report
if /I "%~1"=="EULER_RUN" goto euler_custom
if /I "%~1"=="BUILD_NPZ" goto build_alias
if /I "%~1"=="CERTIFY" goto not_certified
if /I "%~1"=="FREEZE" goto not_certified
if /I "%~1"=="SNAPSHOTS" goto legacy
if /I "%~1"=="DEMO" goto legacy
if /I "%~1"=="BUNDLED" goto legacy
if /I "%~1"=="PKLSA_GEOMETRY" goto legacy
.venv\Scripts\python.exe -m euler_extension.cli %*
exit /b %errorlevel%
:euler_default
.venv\Scripts\python.exe -m euler_extension.cli EULER_RUN
if errorlevel 1 exit /b 1
goto report
:euler_custom
.venv\Scripts\python.exe -m euler_extension.cli %*
if errorlevel 1 exit /b 1
goto report
:build_alias
.venv\Scripts\python.exe -m euler_extension.cli EULER_BUILD %2 %3 %4 %5 %6 %7 %8 %9
exit /b %errorlevel%
:tests
.venv\Scripts\python.exe -m euler_extension.cli EULER_TEST
exit /b %errorlevel%
:report
.venv\Scripts\python.exe -m euler_extension.stretchaudit
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m euler_extension.resolution_screen
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe -m euler_extension.report
exit /b %errorlevel%
:legacy
.venv\Scripts\python.exe -m a064.cli %*
exit /b %errorlevel%
:not_certified
echo A064 v0.2.0 is a prototype: official framework v1.0.7 FREEZE/CERTIFY is NOT integrated.
exit /b 3
