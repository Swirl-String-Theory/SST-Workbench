@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0..\..\.."
if /I "%~1"=="PLAN" (
 echo A006 v0.4.2c ^| combined 3-block XYZ ONLY ^| No KPC or KPT generated.
 echo run_all.cmd BORROMEAN WHOLE BUILD
 echo run_all.cmd BORROMEAN WHOLE BUILD FULL
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED 1024 1024 1165
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED AUTO 3072
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 256 [SCALE] [default 0.80]
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 512 [SCALE]
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 1024 [SCALE]
 echo run_all.cmd BORROMEAN WHOLE BUILD ALL MIN 256 0.80
 echo run_all.cmd BORROMEAN WHOLE TEST
 exit /b 0
)
if /I "%~1"=="TEST" (
 py -3 extensions\borromean\whole\test_whole.py --root "%CD%"
 if errorlevel 1 exit /b 1
 py -3 extensions\borromean\whole\strict_xyz.py --test
 exit /b %errorlevel%
)
if /I "%~1"=="BUILD" (
 if /I "%~3"=="MIN" (
  set "RFSCALE=0.80"
  if not "%~5"=="" set "RFSCALE=%~5"
  if /I "%~2"=="ALL" (
   py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --n-shortest %~4 --global-scale !RFSCALE!
  ) else (
   py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --profiles %~2 --n-shortest %~4 --global-scale !RFSCALE!
  )
 ) else if "%~2"=="" (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --n 1024
 ) else if /I "%~2"=="FULL" (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --n 2048
 ) else if /I "%~3"=="AUTO" (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --profiles %~2 --total-beads %~4
 ) else (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --profiles %~2 --n-per-component %~3 %~4 %~5
 )
 exit /b %errorlevel%
)
if /I "%~1"=="PILOT" (
 echo Import the generated *_v042c.xyz in your existing KnotPlot GUI (no KPC generated).
 echo Check 'close' status after import. KnotPlot 'close all' is available if the XYZ import leaves components open.
 exit /b 0
)
echo Usage: run_all.cmd BORROMEAN WHOLE TEST^|PLAN^|BUILD [FULL^|PROFILE N0 N1 N2^|PROFILE AUTO TOTAL^|PROFILE MIN N [SCALE]]^|PILOT
exit /b 2
