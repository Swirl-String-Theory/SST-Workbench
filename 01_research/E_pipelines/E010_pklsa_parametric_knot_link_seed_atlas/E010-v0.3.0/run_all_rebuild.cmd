@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
set "OUT=%~dp0E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs"
if exist "%OUT%" (
  for /f %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%T"
  set "OLD=%~dp0E010_PKLSA_Production_Knot_Link_Basis_v0.3.0-outputs-superseded-%STAMP%"
  echo [rebuild] Preserving prior scientific output:
  echo           %OUT%
  echo        -^> !OLD!
  move "%OUT%" "!OLD!" >nul || exit /b 20
)
call "%~dp0run_all.cmd" %*
exit /b %ERRORLEVEL%
