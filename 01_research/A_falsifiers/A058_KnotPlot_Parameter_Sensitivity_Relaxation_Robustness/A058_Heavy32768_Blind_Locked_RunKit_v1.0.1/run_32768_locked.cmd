@echo off
setlocal EnableExtensions
set "INSTANCE=%~1"
if "%INSTANCE%"=="" (
  echo Usage: run_32768_locked.cmd "C:\path\to\A058-v0.2.10" [CHECK_ONLY]
  exit /b 2
)
if not exist "%INSTANCE%\run_all.cmd" (
  echo ERROR: A058-v0.2.10 run_all.cmd not found in "%INSTANCE%"
  exit /b 2
)
set "PY=%INSTANCE%\.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo ERROR: Run A058-v0.2.10 installation first; its .venv\Scripts\python.exe is missing
  exit /b 2
)
"%PY%" "%~dp0locked_heavy.py" CHECK "%INSTANCE%"
if errorlevel 1 exit /b 2
if /I "%~2"=="CHECK_ONLY" (
 echo CHECK_ONLY complete. No KnotPlot simulation was started.
 exit /b 0
)
echo LOCK VERIFIED. Starting original A058-v0.2.10 32768 acquisition.
call "%INSTANCE%\run_all.cmd" 32768
if errorlevel 1 (
 echo A058 heavy run returned failure; data and logs remain in original instance.
 exit /b 1
)
"%PY%" "%~dp0locked_heavy.py" VERIFY "%INSTANCE%"
if errorlevel 1 exit /b 2
echo LOCKED 32768 RUN AND SELECTION VERIFICATION COMPLETE.
exit /b 0
