@echo off
setlocal
cd /d "%~dp0..\..\.."
if /I "%~1"=="PLAN" (
 echo A006 v0.4.2 WHOLE COMPONENT: 5_2, 5_2, 6_1.
 echo Uses output\seeds\5_2_N*.kpt and 6_1_N*.kpt; no local knot splices.
 echo Uses reference borromean_flat.txt or borromean_balanced.txt.
 echo One output XYZ per three components, separated by one blank line.
 echo run_all.cmd BORROMEAN WHOLE BUILD        ^(1024 beads/component^)
 echo run_all.cmd BORROMEAN WHOLE BUILD FULL   ^(2048 beads/component^)
 echo run_all.cmd BORROMEAN WHOLE TEST
 echo run_all.cmd BORROMEAN WHOLE PILOT
 exit /b 0
)
if /I "%~1"=="TEST" (
 py -3 extensions\borromean\whole\test_whole.py --root "%CD%"
 exit /b %errorlevel%
)
if /I "%~1"=="BUILD" (
 if /I "%~2"=="FULL" (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --n 2048
 ) else (
  py -3 extensions\borromean\whole\build_whole.py --root "%CD%" --n 1024
 )
 exit /b %errorlevel%
)
if /I "%~1"=="PILOT" (
 echo First run: read output/borromean/Borromean_5_5_6_BALANCED_N1024_LOAD.kpc
 echo Then: read output/borromean/Borromean_5_5_6_BALANCED_N1024_TANF_OFF_PILOT.kpc
 echo To inspect flat: load output/borromean/borromean_flat.txt
 echo To inspect balanced: load output/borromean/borromean_balanced.txt
 echo The filenames are single combined XYZ files with 3 component blocks.
 exit /b 0
)
echo Usage: run_all.cmd BORROMEAN WHOLE TEST^|PLAN^|BUILD [FULL]^|PILOT
exit /b 2
