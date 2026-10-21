@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0..\..\.."
set "WHOLE=extensions\borromean\whole"
if /I "%~1"=="PLAN" (
 echo A006 v0.4.2d: same whole-component XYZ generator; both 5_5_6 and 6_6_5.
 echo run_all.cmd BORROMEAN WHOLE BUILD BALANCED MIN 512 0.80
 echo run_all.cmd BORROMEAN WHOLE BUILD665 BALANCED MIN 512 0.80
 echo run_all.cmd BORROMEAN WHOLE METRICS 665 BALANCED 512 OFF
 echo run_all.cmd BORROMEAN WHOLE ANALYZE
 exit /b 0
)
if /I "%~1"=="TEST" (
 py -3 %WHOLE%\test_whole.py --root "%CD%"
 if errorlevel 1 exit /b 1
 py -3 %WHOLE%\strict_xyz.py --test
 if errorlevel 1 exit /b 1
 py -3 %WHOLE%\test_metrics_patch.py --root "%CD%"
 exit /b !errorlevel!
)
if /I "%~1"=="METRICS_EXT" (
 if "%~5"=="" (echo Usage: ... METRICS_EXT 665 BALANCED 512 OFF^|ON ^(unverified /W and /F^) & exit /b 2)
 py -3 %WHOLE%\metrics_native.py --root "%CD%" --composition %~2 --profile %~3 --n-shortest %~4 --tanf %~5 --extended
 exit /b !errorlevel!
)
if /I "%~1"=="METRICS" (
 if "%~5"=="" (echo Usage: ... METRICS 665 BALANCED 512 OFF^|ON & exit /b 2)
 py -3 %WHOLE%\metrics_native.py --root "%CD%" --composition %~2 --profile %~3 --n-shortest %~4 --tanf %~5
 exit /b !errorlevel!
)
if /I "%~1"=="ANALYZE" (
 py -3 %WHOLE%\analyze_borromean.py --root "%CD%"
 exit /b !errorlevel!
)
if /I "%~1"=="BUILD665" (set "COMPOSITION=665" & goto build)
if /I "%~1"=="BUILD" (set "COMPOSITION=556" & goto build)
if /I "%~1"=="PILOT" (
 echo Open the combined .xyz file DIRECTLY in KnotPlot; no LOAD script generated.
 echo Use METRICS to generate a measurement-only .txt script to read after loading.
 exit /b 0
)
echo Usage: run_all.cmd BORROMEAN WHOLE PLAN^|TEST^|BUILD^|BUILD665^|METRICS^|METRICS_EXT^|ANALYZE
exit /b 2
:build
if /I "%~3"=="MIN" (
 set "RFSCALE=0.80"
 if not "%~5"=="" set "RFSCALE=%~5"
 if /I "%~2"=="ALL" (
  py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --n-shortest %~4 --global-scale !RFSCALE!
 ) else (
  py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --profiles %~2 --n-shortest %~4 --global-scale !RFSCALE!
 )
) else if "%~2"=="" (
 py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --n 1024
) else if /I "%~2"=="FULL" (
 py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --n 2048
) else if /I "%~3"=="AUTO" (
 py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --profiles %~2 --total-beads %~4
) else (
 py -3 %WHOLE%\build_whole.py --root "%CD%" --composition !COMPOSITION! --profiles %~2 --n-per-component %~3 %~4 %~5
)
exit /b !errorlevel!
