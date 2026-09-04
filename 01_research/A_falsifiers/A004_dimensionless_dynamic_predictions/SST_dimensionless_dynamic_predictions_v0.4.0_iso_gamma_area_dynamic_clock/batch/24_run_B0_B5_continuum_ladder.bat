@echo off
setlocal enabledelayedexpansion
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
for %%G in (
  B0_isolated_control
  B1_large_radius_uniform_control
  B2_hole_matched_continuum
  B3_radius_ratio_sweep
  B4_chirality_sweep
  B5_topology_sweep
) do (
  echo.
  echo === %%G ===
  %PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\%%G.json --output outputs\%%G
  if errorlevel 1 goto :fail
)
echo [OK] B0-B5 voltooid.
pause
exit /b 0
:fail
echo [ERROR] B0-B5 afgebroken.
pause
exit /b 1
