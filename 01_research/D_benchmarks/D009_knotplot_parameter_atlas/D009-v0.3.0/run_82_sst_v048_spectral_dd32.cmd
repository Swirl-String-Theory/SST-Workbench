@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not defined SST_V048_DIR set "SST_V048_DIR=C:\workspace\projects\SST-Workbench\SST_Trefoil_Lobe_Orientation_Blind_Falsifier\SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"
if not exist "%SST_V048_DIR%\VERSION.json" (
  echo ERROR: SST v0.4.8 target not found:
  echo   %SST_V048_DIR%
  exit /b 2
)
if not exist "%SST_V048_DIR%\.venv\Scripts\python.exe" (
  echo [SST-BRIDGE] v0.4.8 venv missing - running target installer...
  call "%SST_V048_DIR%\run_install.cmd"
  if errorlevel 1 exit /b %ERRORLEVEL%
)

if not exist "%SST_V048_DIR%\build\sycl_dd32_smoke.json" (
  echo [SST-BRIDGE] DD32 smoke missing - running target smoke first...
  call "%SST_V048_DIR%\run_sycl_dd32_smoke.cmd"
  if errorlevel 1 (
    echo ERROR: DD32 smoke failed. Spectral stage not started.
    exit /b %ERRORLEVEL%
  )
)
"%SST_V048_DIR%\.venv\Scripts\python.exe" sst_v048_adapter.py --mode spectral --target "%SST_V048_DIR%" --backend sycl-dd32
exit /b %ERRORLEVEL%
