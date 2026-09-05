@echo off
setlocal EnableExtensions

rem run_core.cmd — core MultiDynamics discovery matrix (thin wrapper like run_catalog_batch.cmd)
rem
rem   run_core.cmd
rem   run_core.cmd --dry-run

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%run_matrix_batch.py" --core %*
exit /b %ERRORLEVEL%
