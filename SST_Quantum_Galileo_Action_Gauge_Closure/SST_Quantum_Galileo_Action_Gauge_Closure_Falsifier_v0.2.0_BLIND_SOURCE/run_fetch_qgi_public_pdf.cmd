@echo off
setlocal
cd /d "%~dp0"
set "OUT=data\qgi\source\2502.14535v4.pdf"
if exist "%OUT%" (
  echo Public QGI PDF already exists:
  echo   %OUT%
  exit /b 0
)
if not exist "data\qgi\source" mkdir "data\qgi\source"
echo Downloading public arXiv QGI manuscript...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri 'https://arxiv.org/pdf/2502.14535' -OutFile '%OUT%'"
if errorlevel 1 (
  echo ERROR: could not download the public QGI PDF.
  exit /b 1
)
echo Saved:
echo   %OUT%
endlocal
