@echo off
setlocal enabledelayedexpansion
call "%~dp0_common.bat"
if errorlevel 1 exit /b 1
cd /d "%ROOT%"
set PY_CMD="%ROOT%\.venv\Scripts\python.exe"
if not exist "%ROOT%\.venv\Scripts\python.exe" (
  echo [ERROR] Voer eerst batch\01_setup_venv.bat uit.
  pause
  exit /b 1
)
echo Deze pipeline voert de volledige B0-B8-ladder uit. B7 is de grootste campagne.
choice /M "Volledige testladder starten"
if errorlevel 2 exit /b 0
for %%G in (
  B0_isolated_control
  B1_large_radius_uniform_control
  B2_hole_matched_continuum
  B3_radius_ratio_sweep
  B4_chirality_sweep
  B5_topology_sweep
  B6_physical_tubes
  B6_numerical_discretization
  B7_discretization_convergence
  B8_circulation_clock
) do (
  echo.
  echo === %%G ===
  %PY_CMD% src\sst_axial_vortex_bundle.py campaign --config configs\%%G.json --output outputs\%%G
  if errorlevel 1 goto :fail
)
%PY_CMD% tools\analyze_bundle_modes.py --input outputs --output outputs\bundle_mode_analysis
if errorlevel 1 goto :fail
start "" "%ROOT%\outputs\bundle_mode_analysis"
pause
exit /b 0
:fail
echo [ERROR] Volledige ladder werd afgebroken.
pause
exit /b 1
