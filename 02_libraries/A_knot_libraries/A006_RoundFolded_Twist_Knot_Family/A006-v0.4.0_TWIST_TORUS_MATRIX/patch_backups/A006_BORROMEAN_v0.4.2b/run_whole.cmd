@echo off
setlocal
cd /d "%~dp0..\..\.."
if /I "%~1"=="PLAN" (
 echo v0.4.2a WHOLE: native geometry, EXACT ONE PLAIN XYZ with 3 blocks per profile.
 echo Does not generate LOAD.kpc or any other KPC.
 echo RUN: run_all.cmd BORROMEAN WHOLE BUILD [FULL]
 echo Validate: run_all.cmd BORROMEAN WHOLE TEST
 echo Direct files: output\borromean\Borromean_5_5_6_BALANCED_N1024.xyz
 exit /b 0
)
if /I "%~1"=="TEST" (
 py -3 extensions\borromean\whole\test_whole.py --root "%CD%"
 if errorlevel 1 exit /b 1
 py -3 extensions\borromean\whole\strict_xyz.py --test
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
 echo No LOAD scripts are supplied. Import the original numeric XYZ manually in KnotPlot GUI.
 echo Then run your preferred ago/checkpoint commands. KnotPlot coords exports may contain component headers;
 echo use strict_xyz.py --normalize-raw to create a separate strictly numeric analysis copy.
 exit /b 0
)
echo Usage: run_all.cmd BORROMEAN WHOLE TEST^|PLAN^|BUILD [FULL]^|PILOT
exit /b 2
