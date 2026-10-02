@echo off
rem Resolve workbench root into PU_WB (directory containing 07_scripts\paper_upgrade_runtime.py).
rem Optional: set PU_FAMILY PU_TIER PU_OUT before calling :pu_init
goto :eof

:pu_find_wb
set "PU_WB=%CD%"
:pu_find_wb_loop
if exist "%PU_WB%\07_scripts\paper_upgrade_runtime.py" goto :eof
for %%I in ("%PU_WB%\..") do set "PU_WB=%%~fI"
if /I "%PU_WB%"=="%PU_WB_PREV%" (
  echo [paper-upgrade] ERROR: cannot find 07_scripts\paper_upgrade_runtime.py from %CD%
  exit /b 2
)
set "PU_WB_PREV=%PU_WB%"
goto :pu_find_wb_loop

:pu_parse_flags
echo.%*| findstr /I /C:"/resume" >nul && set "SST_RESUME=1"
echo.%*| findstr /I /C:"/fresh" >nul && set "SST_FRESH=1"
goto :eof

:pu_init
call :pu_find_wb
if errorlevel 1 exit /b 1
if not defined PU_FAMILY (
  echo [paper-upgrade] ERROR: PU_FAMILY not set
  exit /b 2
)
if not defined PU_TIER set "PU_TIER=basic"
if not defined PU_OUT set "PU_OUT=outputs\basic"
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" init --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" %PU_RESUME_FLAG%
if errorlevel 1 exit /b 1
goto :eof

:pu_stage
rem usage: call :pu_stage stage_id command...
set "PU_SID=%~1"
shift
call :pu_find_wb
set "PU_RESUME_FLAG="
if /I "%SST_RESUME%"=="1" set "PU_RESUME_FLAG=--resume"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" stage --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --id "%PU_SID%" %PU_RESUME_FLAG% -- %*
exit /b %ERRORLEVEL%

:pu_finish
call :pu_find_wb
set "PU_STATUS=%~1"
if "%PU_STATUS%"=="" set "PU_STATUS=DONE"
python "%PU_WB%\07_scripts\paper_upgrade_runtime.py" finish --family "%PU_FAMILY%" --tier "%PU_TIER%" --out "%PU_OUT%" --status "%PU_STATUS%"
exit /b %ERRORLEVEL%
