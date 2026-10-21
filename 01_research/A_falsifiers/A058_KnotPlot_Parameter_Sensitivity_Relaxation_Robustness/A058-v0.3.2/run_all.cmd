@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="DIST_AUDIT" goto distribution
if /I "%~1"=="KPF_AUDIT" goto distribution
if /I "%~1"=="AUDIT_ALL" goto distribution
if /I "%~1"=="GENERATE_PROBES" goto distribution
if /I "%~1"=="RUN_SAFE_PROBES" goto distribution
if /I "%~1"=="CHECK_SHORTCUT" goto shortcut
if /I "%~1"=="SELFTEST" goto alltests
py -3 bridge.py %*
exit /b %ERRORLEVEL%
:shortcut
py -3 tools\shortcut_check.py %*
exit /b %ERRORLEVEL%
:distribution
py -3 tools\distribution_audit.py %*
exit /b %ERRORLEVEL%
:alltests
py -3 -m unittest discover -s tests -v
if errorlevel 1 exit /b %ERRORLEVEL%
py -3 bridge.py SELFTEST
exit /b %ERRORLEVEL%
