@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call config\paths.cmd
if not defined KK_PY (
  echo [KK-SST] No shared/local venv found. Creating local .venv ...
  where py >nul 2>nul
  if not errorlevel 1 (
    py -3 -m venv .venv
  ) else (
    python -m venv .venv
  )
  if errorlevel 1 exit /b 1
  set "KK_PY=%CD%\.venv\Scripts\python.exe"
)
echo [KK-SST] Python: "%KK_PY%"
"%KK_PY%" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
"%KK_PY%" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
"%KK_PY%" -m kk_native.build_ext_if_needed --force --strict
if errorlevel 1 (
  echo [KK-SST] Native build failed. See the compiler diagnostics above.
echo [KK-SST] If cl.exe is not found, install VS2022 Desktop development with C++.
echo [KK-SST] If cl.exe is found, this is a source/build error rather than a missing compiler.
  exit /b 1
)
echo [KK-SST] INSTALL PASS
endlocal
