@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_install.cmd
if errorlevel 1 exit /b %errorlevel%
set "PY=%CD%\.venv\Scripts\python.exe"
if not defined SST_NATIVE_THREADS set "SST_NATIVE_THREADS=16"
"%PY%" -m native_ext.build_ext_if_needed --strict
if errorlevel 1 (
  echo [4_SST] ERROR: native C++ backend could not be built.
  echo [4_SST] Install Visual Studio C++ Build Tools / Desktop development with C++ and rerun.
  exit /b 1
)
"%PY%" -c "from native_ext import set_num_threads,backend_info; set_num_threads(%SST_NATIVE_THREADS%); print(backend_info())"
exit /b %ERRORLEVEL%
