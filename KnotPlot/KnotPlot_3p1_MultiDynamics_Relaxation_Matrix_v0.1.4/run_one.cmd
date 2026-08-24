@echo off
setlocal EnableExtensions

rem run_one.cmd — single MultiDynamics .kpc (thin wrapper like run_catalog_batch.cmd)
rem
rem   run_one.cmd 10_force_ablation_matrix.kpc
rem   run_one.cmd smoke_load_3_1.kpc
rem   run_one.cmd catalog\knot_0.1\build_knot_0.1.kpc
rem   run_one.cmd 00_baseline_MEB_tight.kpc --dry-run

set "BUNDLE=%~dp0"

if "%~1"=="" (
  echo Usage: run_one.cmd ^<script.kpc^> [--dry-run]
  echo Example: run_one.cmd 10_force_ablation_matrix.kpc
  echo Example: run_one.cmd smoke_load_3_1.kpc
  exit /b 2
)

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%run_matrix_batch.py" --one %*
exit /b %ERRORLEVEL%
