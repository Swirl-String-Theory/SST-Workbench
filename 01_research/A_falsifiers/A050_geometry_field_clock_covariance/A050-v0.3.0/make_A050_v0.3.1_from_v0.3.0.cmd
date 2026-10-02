@echo off
setlocal EnableExtensions
set "SRC=%~1"
if not defined SRC set "SRC=%CD%"
for %%I in ("%SRC%") do set "SRC=%%~fI"
if not exist "%SRC%\project.json" (
  echo ERROR: source must be the A050-v0.3.0 directory.
  exit /b 2
)
for %%I in ("%SRC%\..") do set "PARENT=%%~fI"
set "DST=%PARENT%\A050-v0.3.1"
if exist "%DST%" (
  echo ERROR: target already exists: "%DST%"
  exit /b 3
)
echo Copying A050-v0.3.0 to A050-v0.3.1 ...
robocopy "%SRC%" "%DST%" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD .venv .pytest_cache __pycache__ /XF *.pyc >nul
if errorlevel 8 (
  echo ERROR: robocopy failed.
  exit /b 4
)
pushd "%DST%"
git apply --check "%~dp0A050-v0.3.1.patch" || (popd & exit /b 5)
git apply "%~dp0A050-v0.3.1.patch" || (popd & exit /b 6)
popd
echo.
echo Created: "%DST%"
echo Next: cd /d "%DST%" ^&^& run_all.cmd C:\workspace\projects\SST-Workbench
endlocal
