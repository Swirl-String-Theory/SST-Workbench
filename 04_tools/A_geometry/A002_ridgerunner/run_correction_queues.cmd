@echo off
setlocal EnableExtensions

rem run_correction_queues.cmd — Fase-B re-runs after KnotPlot build corrections
rem
rem Queues (default: all correction queues except skip):
rem   unfinished  link_6.3.3,link_7.2.5,torus_2.6
rem   continue    knot_5.1,knot_5.2,knot_6.1,torus_3.3
rem   legacy-links  (all link_* with stalled/legacy Stop20 min runs)
rem   status-only link_4.2.1  (reclassify+resample; use --status-only)
rem
rem knot_0.1 is intentionally skipped (analytic circle is canonical).
rem
rem Examples:
rem   run_correction_queues.cmd --dry-run
rem   run_correction_queues.cmd --queue unfinished -t8
rem   run_correction_queues.cmd --queue continue,legacy-links -t8

set "BUNDLE=%~dp0"

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH
  exit /b 1
)

python "%BUNDLE%run_correction_queues.py" %*
exit /b %ERRORLEVEL%
