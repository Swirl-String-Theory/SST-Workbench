@echo off
setlocal
cd /d "%~dp0..\.."
if /I "%~1"=="TEST" (
 py -3 extensions\borromean\test_borromean.py --root "%CD%"
 exit /b %errorlevel%
)
if /I "%~1"=="PLAN" (
 echo v0.4.1 BORROMEAN: 5_2+5_2+6_1; source from output\seeds; no existing runs modified.
 echo run_all.cmd BORROMEAN BUILD          -- SOFT, BALANCED, TIGHT; 1024 beads per component
 echo run_all.cmd BORROMEAN BUILD FULL     -- experimental 2048 beads per component
 echo run_all.cmd BORROMEAN PILOT         -- display manual atomic ago script paths
 exit /b 0
)
if /I "%~1"=="BUILD" (
 if /I "%~2"=="FULL" (
  py -3 extensions\borromean\build_borromean.py --root "%CD%" --n 2048
 ) else (
  py -3 extensions\borromean\build_borromean.py --root "%CD%" --n 1024
 )
 exit /b %errorlevel%
)
if /I "%~1"=="PILOT" (
 echo Use KnotPlot GUI with the EXISTING shortcut and project root working directory.
 echo Please run the generated *_TANF_OFF_PILOT.kpc first, one profile at a time.
 echo Example: read output/borromean_55261/Borromean_5_2_5_2_6_1_SOFT_N1024/Borromean_5_2_5_2_6_1_SOFT_N1024_TANF_OFF_PILOT.kpc
 exit /b 0
)
echo Usage: run_all.cmd BORROMEAN TEST^|PLAN^|BUILD [FULL]^|PILOT
exit /b 2
