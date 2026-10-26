@echo off
setlocal EnableExtensions
rem P7 v0.7.2 CMD installer; preserves local package.json; Python 3 and Node.js required
where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0Apply-P7.2.py" %*
) else (
    python "%~dp0Apply-P7.2.py" %*
)
set "status=%errorlevel%"
if not "%status%"=="0" echo INSTALLATION FAILED, EXIT CODE %status%
exit /b %status%
