@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m triadic.launch %*
) else (
    python -m triadic.launch %*
)
set "RC=%ERRORLEVEL%"
echo.
echo Distinct run artifacts: "%~dp0exports\"
echo Archive of run workspaces: "%~dp0runs\"
exit /b %RC%
