@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="SELFTEST" (
    py -3 -m pytest -q tests
    exit /b %errorlevel%
)
if /I "%~1"=="PRECHECK" (
    py -3 -m a060_preflight --source-dir "%~2" --out "preflight_outputs"
    exit /b %errorlevel%
)
echo Usage: run_preflight.cmd SELFTEST
 echo        run_preflight.cmd PRECHECK "C:\path\to\paper-pdfs"
exit /b 1
