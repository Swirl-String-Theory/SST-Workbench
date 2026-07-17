@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem run_build.cmd — KnotPlot build_*.kpc via KnotPlot.lnk, optional -rr pipeline
rem
rem   run_build.cmd torus_6.9
rem   run_build.cmd knot_4.1 -rr
rem   run_build.cmd torus_6.9 -rr --seed trial_009k
rem   run_build.cmd knot_3.1 -rr --multistart
rem   run_build.cmd link_0.2.1 -rr --allow-unverified-topology

set "ROOT=%~dp0"
set "LNK=%ROOT%KnotPlot.lnk"
set "NOG=-nog"
set "DO_RR="
set "ARG="
set "SEED_OPT="
set "MULTISTART="
set "ALLOW_UNVERIFIED="

if not exist "%LNK%" (
  echo ERROR: KnotPlot.lnk not found at "%LNK%"
  exit /b 1
)

:parse
if "%~1"=="" goto after_parse
if /I "%~1"=="/gui" (
  set "NOG="
  shift
  goto parse
)
if /I "%~1"=="/list" (
  call :list_builds
  exit /b 0
)
if /I "%~1"=="-rr" (
  set "DO_RR=1"
  shift
  goto parse
)
if /I "%~1"=="--ridgerunner" (
  set "DO_RR=1"
  shift
  goto parse
)
if /I "%~1"=="--seed" (
  if "%~2"=="" (
    echo ERROR: --seed requires a value ^(analytic ^| trial_005k ^| ...^)
    exit /b 1
  )
  set "SEED_OPT=%~2"
  shift
  shift
  goto parse
)
if /I "%~1"=="--multistart" (
  set "MULTISTART=1"
  shift
  goto parse
)
if /I "%~1"=="--allow-unverified-topology" (
  set "ALLOW_UNVERIFIED=1"
  shift
  goto parse
)
if /I "%~1"=="/h" (
  call :HELP
  exit /b 1
)
if /I "%~1"=="/?" (
  call :HELP
  exit /b 1
)
if /I "%~1"=="-h" (
  call :HELP
  exit /b 1
)
if /I "%~1"=="--help" (
  call :HELP
  exit /b 1
)
set "ARG=%~1"
shift
goto parse

:after_parse
if not defined ARG (
  call :HELP
  exit /b 1
)

for /f "usebackq delims=" %%A in (`powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); Write-Output $s.TargetPath; Write-Output $s.WorkingDirectory"`) do (
  if not defined KP_EXE (
    set "KP_EXE=%%A"
  ) else if not defined KP_CWD (
    set "KP_CWD=%%A"
  )
)

if not defined KP_CWD set "KP_CWD=%ROOT%"
if not exist "%KP_EXE%" (
  echo ERROR: KnotPlot.exe from shortcut not found: "%KP_EXE%"
  exit /b 1
)

call :resolve_script "%ARG%"
if not defined SCRIPT (
  echo ERROR: could not resolve build script for "%ARG%"
  echo Use /list to see available scripts.
  exit /b 1
)
if not exist "%SCRIPT%" (
  echo ERROR: script not found: "%SCRIPT%"
  exit /b 1
)

for %%F in ("%SCRIPT%") do set "OUTDIR=%%~dpF"
rem Trailing backslash breaks "...\dir\" quoting in Python/PowerShell args
if "!OUTDIR:~-1!"=="\" set "OUTDIR=!OUTDIR:~0,-1!"
set "LOG=!OUTDIR!\build_knotplot.log"

pushd "%KP_CWD%" || exit /b 1

echo KnotPlot: "%KP_EXE%"
echo CWD:      "%CD%"
echo Script:   "%SCRIPT%"
echo Log:      "%LOG%"
if defined NOG (
  echo Mode:     non-graphics ^(-nog^)
  "%KP_EXE%" -nog < "%SCRIPT%" > "%LOG%" 2>&1
) else (
  echo Mode:     GUI
  "%KP_EXE%" < "%SCRIPT%" > "%LOG%" 2>&1
)
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
  echo ERROR: KnotPlot failed, see "%LOG%"
  exit /b %RC%
)

rem Parse CHECKPOINT blocks → *.knotplot.json sidecars
where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: python not found on PATH ^(needed for sidecars / seed selection^)
  exit /b 1
)
python "%ROOT%ridgerunner\parse_knotplot_log.py" "!OUTDIR!" --log "!LOG!"
if errorlevel 1 (
  if defined DO_RR (
    echo ERROR: sidecar parse failed — aborting -rr. See parser output above.
    exit /b 1
  )
  echo WARNING: sidecar parse failed; continuing without -rr sidecars
)

if not defined DO_RR (
  echo KnotPlot build finished. Log: "!LOG!"
  exit /b 0
)

set "RR_PIPE=%ROOT%ridgerunner\run_three_stage.cmd"
set "SELECT=%ROOT%ridgerunner\select_knotplot_seed.py"
if not exist "%RR_PIPE%" (
  echo ERROR: missing "%RR_PIPE%"
  exit /b 1
)

set "SEL_ARGS=!OUTDIR!"
if defined SEED_OPT set "SEL_ARGS=!SEL_ARGS! --seed !SEED_OPT!"
if defined ALLOW_UNVERIFIED set "SEL_ARGS=!SEL_ARGS! --allow-unverified-topology"

echo.
echo ============================================================
echo Selecting KnotPlot seed for ridgerunner...
echo ============================================================
python "%SELECT%" !SEL_ARGS!
if errorlevel 1 (
  echo ERROR: seed selection failed
  exit /b 1
)

rem Read selected path from seed_selection.json
for /f "usebackq delims=" %%S in (`powershell -NoProfile -Command "$j=Get-Content -Raw '!OUTDIR!\seed_selection.json' | ConvertFrom-Json; if ($j.selected) { $j.selected } else { exit 2 }"`) do set "SELECTED=%%S"
if not defined SELECTED (
  echo ERROR: no seed selected ^(see "!OUTDIR!\seed_selection.json"^)
  exit /b 1
)

echo Selected seed: !SELECTED!
call "%RR_PIPE%" "!SELECTED!"
if errorlevel 1 exit /b 1

if defined MULTISTART (
  for %%A in ("!OUTDIR!\*_analytic_D1.txt") do (
    if exist "%%~fA" (
      echo.%%~nxA| findstr /I /C:"_rr_" >nul
      if errorlevel 1 (
        if /I not "%%~fA"=="!SELECTED!" (
          echo.
          echo ---- multistart analytic: %%~nxA ----
          call "%RR_PIPE%" "%%~fA"
          if errorlevel 1 exit /b 1
        )
      )
    )
  )
)

echo.
echo Ridgerunner pipeline finished ^(polish + VortexLab uniform N=300^).
exit /b 0

:resolve_script
set "SCRIPT="
set "RAW=%~1"

if exist "%RAW%" (
  for %%F in ("%RAW%") do set "SCRIPT=%%~fF"
  goto :eof
)
if exist "%ROOT%%RAW%" (
  for %%F in ("%ROOT%%RAW%") do set "SCRIPT=%%~fF"
  goto :eof
)

set "ID=%RAW%"
if /I "!ID:~0,11!"=="build_knot_" set "ID=!ID:~11!"
if /I "!ID:~0,11!"=="build_link_" set "ID=!ID:~11!"
if /I "!ID:~0,12!"=="build_torus_" set "ID=!ID:~12!"
if /I "!ID:~0,12!"=="build_Tlink_" set "ID=Tlink_!ID:~12!"
rem knot_ and link_ are 5 chars; torus_ and Tlink_ are 6
if /I "!ID:~0,5!"=="knot_" set "ID=!ID:~5!"
if /I "!ID:~0,5!"=="link_" set "ID=!ID:~5!"
if /I "!ID:~0,6!"=="torus_" set "ID=!ID:~6!"
if /I "!ID:~0,6!"=="Tlink_" set "ID=Tlink_!ID:~6!"

echo.!ID!| findstr /I /B /C:"Tlink" >nul
if not errorlevel 1 (
  if exist "%ROOT%knots\Tlink_6_9\build_Tlink_6_9.kpc" (
    set "SCRIPT=%ROOT%knots\Tlink_6_9\build_Tlink_6_9.kpc"
  )
  goto :eof
)

set "ID=!ID:_=.!"

if exist "%ROOT%knots\knot_!ID!\build_knot_!ID!.kpc" (
  set "SCRIPT=%ROOT%knots\knot_!ID!\build_knot_!ID!.kpc"
  goto :eof
)
if exist "%ROOT%knots\link_!ID!\build_link_!ID!.kpc" (
  set "SCRIPT=%ROOT%knots\link_!ID!\build_link_!ID!.kpc"
  goto :eof
)
if exist "%ROOT%knots\torus_!ID!\build_torus_!ID!.kpc" (
  set "SCRIPT=%ROOT%knots\torus_!ID!\build_torus_!ID!.kpc"
  goto :eof
)
goto :eof

:list_builds
echo Available build scripts under "%ROOT%knots":
for /r "%ROOT%knots" %%F in (build_*.kpc) do echo   %%~nxF  ^(%%F^)
goto :eof

:HELP
echo.
echo Usage: run_build.cmd [options] ^<id^>
echo.
echo   id examples: knot_3.1  link_0.2.1  torus_6.9  Tlink_6_9
echo.
echo Options:
echo   /gui                         graphics mode
echo   /list                        list build_*.kpc
echo   -rr / --ridgerunner          select one seed + 3-stage ridgerunner
echo   --seed analytic or trial_00Nk  force seed
echo   --multistart                 also run analytic after selected trial
echo   --allow-unverified-topology  continue if KnotPlot sidecars incomplete
echo.
echo Without -rr: KnotPlot only (15k checkpoints, log + sidecars).
echo With -rr: checkpoint gate picks one trial, 3-stage RR, then
echo   VortexLab uniform resample (*_polish_uniform_N300.txt + VECT).
echo   Ridgerunner polish TXT is kept unchanged as audit reference.
goto :eof