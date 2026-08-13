@echo off
setlocal EnableExtensions

rem sync_shared_finals.cmd — backfill knots\final\{id}_final.* from historical finals
rem
rem   sync_shared_finals.cmd
rem   sync_shared_finals.cmd --kind knot
rem   sync_shared_finals.cmd --ids knot_3.1,torus_6.9 --dry-run

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%sync_shared_finals.py" %*
exit /b %ERRORLEVEL%
