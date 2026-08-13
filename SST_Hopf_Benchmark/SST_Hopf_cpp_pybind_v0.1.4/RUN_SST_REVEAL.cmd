@echo off
setlocal
cd /d "%~dp0"
if not exist "results\blind\SEALED_MANIFEST.json" (
  echo ERROR: blind results are not sealed.
  exit /b 1
)
if not exist "sst_reveal.json" (
  echo No sst_reveal.json found.
  echo Copy sst_reveal.template.json to sst_reveal.json and fill it now, after sealing.
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" call "cmd\00_SETUP_VENV.cmd"
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe run_sst_reveal.py
exit /b %errorlevel%
