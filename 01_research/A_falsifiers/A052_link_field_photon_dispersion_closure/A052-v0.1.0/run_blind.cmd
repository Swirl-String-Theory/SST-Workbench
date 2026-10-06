@echo off
setlocal EnableExtensions
cd /d "%~dp0"

for %%F in (
  "configs\blind_config.json"
  "data\public\admissibility.json"
) do (
  if not exist "%%~F" (
    echo [A052][ERROR] Missing required input: %%~F
    echo [A052][ERROR] Sync/download the complete A052-v0.1.0 folder before running.
    exit /b 2
  )
)

if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
python -m a052_lfpdcf.run --mode blind --root . --outputs outputs
if errorlevel 1 goto :fail

echo [A052] Blind run completed. Read outputs\blind\verdict.json
exit /b 0

:fail
echo [A052][ERROR] Blind run failed.
exit /b 1
