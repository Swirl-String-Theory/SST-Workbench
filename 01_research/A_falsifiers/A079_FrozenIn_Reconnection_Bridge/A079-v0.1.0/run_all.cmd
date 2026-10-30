@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  if exist "inputs\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip" (
    python run_all.py FULL --e011-zip "inputs\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip" --e011-sha256 "inputs\E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs.zip.sha256"
  ) else (
    python run_all.py FULL
  )
) else (
  python run_all.py %*
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
