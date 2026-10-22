@echo off
setlocal
cd /d "%~dp0"
if /I "%~1"=="FORCEQUAL" goto forcequal
if /I "%~1"=="FORCEGRID" goto forcegrid
if /I "%~1"=="TEST" goto test
if /I "%~1"=="ALIASES" goto aliases
if /I "%~1"=="PREFLIGHT" goto preflight
if /I "%~1"=="ANALYZE" goto analyze
if /I "%~1"=="BUILD" goto build
if /I "%~1"=="CAMPAIGNS" goto campaigns
if /I "%~1"=="BASIC" goto basic
if /I "%~1"=="SMALL" goto small
if /I "%~1"=="MEDIUM" goto medium
if /I "%~1"=="FULL" goto full
if "%~1"=="" goto usage
py -3 tools\selection_v050.py %*
exit /b %errorlevel%
:build
py -3 tools\selection_v050.py --knots=ALL --links=ALL --minN=256 --maxN=2048 --linkProfiles=ALL --mirrored=BOTH --tanf=BOTH --maxIteration=8000 --checkpointsEvery=500 --prepare
if errorlevel 1 exit /b 1
py -3 tools\aliases_v050.py
exit /b %errorlevel%
:campaigns
py -3 tools\selection_v050.py --knots=ALL --links=ALL --minN=256 --maxN=2048 --linkProfiles=ALL --mirrored=BOTH --tanf=BOTH --maxIteration=8000 --checkpointsEvery=500 --prepare
exit /b %errorlevel%
:aliases
py -3 tools\aliases_v050.py
exit /b %errorlevel%
:test
py -3 tools\verify_v050.py
if errorlevel 1 exit /b 1
py -3 tools\topology_check_v050.py
exit /b %errorlevel%
:preflight
py -3 tools\preflight_v050.py
exit /b %errorlevel%
:analyze
py -3 tools\analysis_v050.py --root .
exit /b %errorlevel%
:basic
py -3 tools\selection_v050.py --knots=5_2,6_1 --links=NONE --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --prepare
exit /b %errorlevel%
:small
py -3 tools\selection_v050.py --knots=3_1,4_1,5_2,6_1 --links=NONE --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --prepare
exit /b %errorlevel%
:medium
py -3 tools\selection_v050.py --knots=3_1,4_1,5_1,5_2,6_1,7_1,7_2,8_1 --links=NONE --minN=256 --maxN=2048 --tanf=BOTH --maxIteration=16000 --checkpointsEvery=500 --prepare
exit /b %errorlevel%
:full
py -3 tools\selection_v050.py --knots=ALL --links=ALL --minN=256 --maxN=2048 --tanf=BOTH --maxIteration=32000 --checkpointsEvery=500 --prepare
exit /b %errorlevel%
:forcegrid
py -3 tools\force_grid_v050c.py %2 %3 %4 %5 %6 %7 %8 %9
exit /b %errorlevel%
:forcequal
py -3 tools\force_qualification_v050b.py %2 %3 %4 %5 %6 %7 %8 %9
exit /b %errorlevel%
:usage
echo A006 v0.5.0: run_all.cmd BUILD^|ALIASES^|TEST^|PREFLIGHT^|ANALYZE
 echo run_all.cmd --knots=ALL --links=ALL --minN=256 --maxN=2048 --maxIteration=8000 --checkpointsEvery=500 --mirrored=BOTH --plan^|--prepare^|--execute
exit /b 2
