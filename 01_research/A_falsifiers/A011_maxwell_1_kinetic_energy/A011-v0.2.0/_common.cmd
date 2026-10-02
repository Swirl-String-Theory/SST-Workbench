@echo off
set "PACKAGE_ROOT=%~dp0"
call "%PACKAGE_ROOT%config\paths.cmd"

set "PYTHON_EXE="
if defined SST_PYTHON if exist "%SST_PYTHON%" set "PYTHON_EXE=%SST_PYTHON%"
if not defined PYTHON_EXE if exist "%SST_SHARED_VENV%\Scripts\python.exe" set "PYTHON_EXE=%SST_SHARED_VENV%\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%PACKAGE_ROOT%.venv\Scripts\python.exe" set "PYTHON_EXE=%PACKAGE_ROOT%.venv\Scripts\python.exe"
if not defined PYTHON_EXE (
  where py >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=py"
)
if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)
if not defined PYTHON_EXE (
  echo [ERROR] No Python interpreter found.
  exit /b 1
)

set "PYTHONPATH=%PACKAGE_ROOT%src;%PYTHONPATH%"
echo [1_MaxwellSST] Python: %PYTHON_EXE%
echo [1_MaxwellSST] Knots : %SST_KNOT_DIR%
echo [1_MaxwellSST] Threads: %SST_NATIVE_THREADS%
exit /b 0
