@echo off
setlocal EnableExtensions

rem run_finalize_knotplot.cmd — scan KnotPlot\knots → build_*_final_* next to .kpc
rem
rem   run_finalize_knotplot.cmd
rem   run_finalize_knotplot.cmd --effort min
rem   run_finalize_knotplot.cmd --kind knot,link,torus --suffix backlog
rem   run_finalize_knotplot.cmd --ids knot_3.1,torus_6.9 --dry-run
rem
rem Does not re-run KnotPlot or Ridgerunner. Summary: out\finalize_knotplot_summary.json

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%run_finalize_knotplot.py" %*
exit /b %ERRORLEVEL%
