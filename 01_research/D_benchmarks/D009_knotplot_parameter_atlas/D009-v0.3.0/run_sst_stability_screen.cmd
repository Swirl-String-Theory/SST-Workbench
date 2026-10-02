@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
if not exist "%SST_V048_DIR%\VERSION.json" (
  echo ERROR: SST v0.4.8 target not found:
  echo   %SST_V048_DIR%
  exit /b 2
)
if not exist "%SST_V048_DIR%\.venv\Scripts\python.exe" (
  echo [SST-BRIDGE] v0.4.8 venv missing - running target installer...
  call "%SST_V048_DIR%\run_install.cmd"
  if errorlevel 1 exit /b %ERRORLEVEL%
)

if not exist stability_handoff\stability_candidates_screen.csv (
  call run_reanalyze_shape_and_prepare_stability.cmd
  if errorlevel 1 exit /b %ERRORLEVEL%
)
call run_80_sst_v048_preflight.cmd
if errorlevel 1 exit /b %ERRORLEVEL%
call run_81_sst_v048_screen_fp64.cmd
exit /b %ERRORLEVEL%
