@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" (
  echo Usage: RUN_RIDGERUNNER_CONVERGENCE.bat "C:\path\to\trefoil_polish.txt"
  pause
  exit /b 1
)
py -3 -m pip install -e . --no-build-isolation
if errorlevel 1 goto :error
py -3 -m sstcbhf convergence --input "%~1" --resolutions 128 192 256 384 --out outputs\ridgerunner_3_1_convergence
set RC=%ERRORLEVEL%
pause
exit /b %RC%
:error
echo Installation failed.
pause
exit /b 1
