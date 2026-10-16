@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "TIER=%~1"
if "%TIER%"=="" set "TIER=pilot"
set "KP=%~2"
set "STARTIN=%~3"

rem Resolution order is implemented by the Python runner:
rem   EXE: arg2 -> KNOTPLOT_EXE -> USER_PROFILE -> USERPROFILE
rem   CWD: arg3 -> KNOTPLOT_STARTIN -> %%SST_WORKBENCH%%\04_tools\A_geometry\A001_knotplot -> outputs fallback
if "%KP%"=="" (
  if "%STARTIN%"=="" (
    call run_python.cmd tools\run_knotplot_campaign.py --tier %TIER%
  ) else (
    call run_python.cmd tools\run_knotplot_campaign.py --tier %TIER% --workdir "%STARTIN%"
  )
) else (
  if "%STARTIN%"=="" (
    call run_python.cmd tools\run_knotplot_campaign.py --tier %TIER% --exe "%KP%"
  ) else (
    call run_python.cmd tools\run_knotplot_campaign.py --tier %TIER% --exe "%KP%" --workdir "%STARTIN%"
  )
)
exit /b %ERRORLEVEL%
