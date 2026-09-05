@echo off
setlocal EnableExtensions
pushd "%~dp0"
call "%~dp0_common.cmd" || goto :fail

rem If no shared/local venv exists and _common fell back to py/python, create a local venv.
if /I "%PYTHON_EXE%"=="py" goto :makevenv
if /I "%PYTHON_EXE%"=="python" goto :makevenv
goto :install

:makevenv
echo [Einstein-SST] Creating local .venv...
%PYTHON_EXE% -m venv "%~dp0.venv" || goto :fail
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"

:install
echo ============================================================
echo [Einstein-SST] Install/update dependencies
ECHO ============================================================
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 echo [WARN] pip/setuptools/wheel upgrade failed; continuing with installed versions.
"%PYTHON_EXE%" -m pip install -r requirements.txt || goto :fail
"%PYTHON_EXE%" run_dependency_preflight.py || goto :fail

echo [Einstein-SST] Building native C++17 backend...
set "SST_OPENMP=1"
"%PYTHON_EXE%" -m sst_einstein.build_ext_if_needed --force || goto :fail

echo [Einstein-SST] Running Python reference unit tests...
"%PYTHON_EXE%" -m unittest tests.test_reference -q || goto :fail

echo [OK] Installation complete.
popd
exit /b 0
:fail
echo [ERROR] Install/check failed with code %errorlevel%.
popd
exit /b 1
