@echo off
setlocal
cd /d "%~dp0"
where py >NUL 2>&1
if %errorlevel%==0 (
    py -3.14 -B -m pklsa_bridge.cli %*
) else (
    python -B -m pklsa_bridge.cli %*
)
exit /b %errorlevel%
