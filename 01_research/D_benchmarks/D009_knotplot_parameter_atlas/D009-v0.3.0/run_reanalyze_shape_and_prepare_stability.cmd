@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo KnotPlot Atlas v0.3.3 - SHAPE CANONICAL + SST HANDOFF
echo ============================================================

if not exist out\extended (
  echo ERROR: out\extended is missing. Complete the v0.3.2 extended stage first.
  exit /b 2
)

call run_50_shape_canonical_extended.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_60_prepare_sst_stability_handoff.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_70_discover_sst_v048_interface.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

call run_90_pack_outputs.cmd
if errorlevel 1 exit /b %ERRORLEVEL%

echo ============================================================
echo DONE
echo Shape report : analysis\SHAPE_CANONICAL_EXTENDED.md
echo SST handoff  : stability_handoff\stability_candidates_screen.csv
echo v0.4.8 scan  : analysis\SST_V048_DISCOVERY.md
echo ============================================================
exit /b 0
