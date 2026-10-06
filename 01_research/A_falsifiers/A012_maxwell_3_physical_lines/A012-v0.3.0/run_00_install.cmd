@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
if defined SST_SHARED_VENV (set "VENV=%SST_SHARED_VENV%") else (set "VENV=%~dp0.venv")
set "PY=%VENV%\Scripts\python.exe"
if not defined SST_WORKBENCH_ROOT if exist "C:\workspace\projects\SST-Workbench" set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "FORCE_PKLSA_REINSTALL=0"
if /I "%~1"=="--force-pklsa-reinstall" set "FORCE_PKLSA_REINSTALL=1"
if defined SST_PKLSA_FORCE_REBUILD set "FORCE_PKLSA_REINSTALL=1"
echo ============================================================
echo 3_MAXWELL v0.3.0 - idempotent install + native checks
echo ============================================================
if not exist "%PY%" (
  echo [3_MAXWELL] Creating venv: "%VENV%"
  where py >nul 2>&1 || (echo ERROR: Python launcher 'py' not found.& exit /b 2)
  py -m venv "%VENV%" || exit /b 2
)
"%PY%" -m pip install --upgrade pip setuptools wheel || exit /b 2
"%PY%" -m pip install -r requirements.txt || exit /b 2
"%PY%" -m pip install -e . --no-build-isolation || exit /b 2

if defined SST_WORKBENCH_ROOT (
  set "PKLSA_FAMILY=%SST_WORKBENCH_ROOT%\01_research\E_pipelines\E010_pklsa_parametric_knot_link_seed_atlas"
  set "PKLSA_RELEASE="
  if exist "!PKLSA_FAMILY!" for /f "usebackq delims=" %%D in (`powershell -NoProfile -Command "Get-ChildItem -LiteralPath '!PKLSA_FAMILY!' -Directory -Filter 'E010-v0.3.*' ^| Sort-Object {[version]($_.Name -replace 'E010-v','')} -Descending ^| Select-Object -First 1 -ExpandProperty FullName"`) do set "PKLSA_RELEASE=%%D"
  if not defined PKLSA_RELEASE (
    echo ERROR: no E010-v0.3.x release found under !PKLSA_FAMILY!
    exit /b 3
  )

  set "PKLSA_READY=0"
  if "!FORCE_PKLSA_REINSTALL!"=="0" (
    "%PY%" -m sst_maxwell3_blind.pklsa_install_probe --release "!PKLSA_RELEASE!" --quiet >nul 2>&1
    if not errorlevel 1 set "PKLSA_READY=1"
  )

  if "!PKLSA_READY!"=="1" (
    echo [3_MAXWELL] E010 PKLSA already active from selected release with native backend.
    echo [3_MAXWELL] Reusing existing editable/native install; no .pyd overwrite required.
  ) else (
    echo [3_MAXWELL] Installing/building E010 PKLSA from: !PKLSA_RELEASE!
    "%PY%" -m pip install -e "!PKLSA_RELEASE!" --no-build-isolation
    if errorlevel 1 (
      echo ERROR: E010 PKLSA editable/native install failed.
      echo [3_MAXWELL] If the error says Access is denied for pklsa_builder\_native*.pyd,
      echo [3_MAXWELL] another Python process has that DLL open. Close Python consoles/processes using this venv and retry.
      echo [3_MAXWELL] If BASIC already passed and E010 has not changed, you can also run:
      echo [3_MAXWELL]   run_01_preflight.cmd extended
      echo [3_MAXWELL]   run_03_extended.cmd
      exit /b 3
    )
  )
) else (
  echo [3_MAXWELL] SST_WORKBENCH_ROOT is not set; E010 will be resolved at preflight.
  echo [3_MAXWELL] Extended/certification require an E010 native backend built for this Python.
)

echo [3_MAXWELL] Building independent Maxwell-3 C++/OpenMP kernel...
"%PY%" -m sst_maxwell3_blind.build_ext_if_needed --force --strict
if errorlevel 1 (
  echo ERROR: Maxwell-3 native build failed. Install VS2022 Build Tools + Desktop development with C++.
  exit /b 4
)
"%PY%" -m sst_maxwell3_blind.cli selftest --native --threads 16
if errorlevel 1 exit /b 5
echo [3_MAXWELL] INSTALL + NATIVE SELFTEST PASS
exit /b 0
