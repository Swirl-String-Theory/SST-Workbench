@echo off
REM Resolve SST_PYTHON for GPU launchers. Call as: call set_sst_python.cmd
REM Intentionally no setlocal so SST_PYTHON remains visible to the caller.

if defined SST_PYTHON goto :verify

set "SST_GPU_LANE="
set "_SST_ENV_FILE=%~dp0.env"
if exist "%_SST_ENV_FILE%" (
  for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%_SST_ENV_FILE%") do (
    if /I "%%~A"=="SST_PYTHON" set "SST_PYTHON=%%~B"
    if /I "%%~A"=="SST_GPU_LANE" set "SST_GPU_LANE=%%~B"
    if /I "%%~A"=="SST_WORKBENCH_ROOT" set "SST_WORKBENCH_ROOT=%%~B"
  )
)

if defined SST_PYTHON goto :verify

if not defined SST_GPU_LANE set "SST_GPU_LANE=xpu"

set "WB="
if defined SST_WORKBENCH_ROOT (
  set "WB=%SST_WORKBENCH_ROOT%"
  goto :map_lane
)

set "_CAND=%~dp0"
:walk
if exist "%_CAND%.venv-a075-xpu\Scripts\python.exe" (
  set "WB=%_CAND%"
  goto :map_lane
)
if exist "%_CAND%catalog_index.json" (
  set "WB=%_CAND%"
  goto :map_lane
)
for %%I in ("%_CAND%..") do set "_NEXT=%%~fI\"
if /I "%_NEXT%"=="%_CAND%" (
  echo ERROR: Could not find SST-Workbench root from "%~dp0"
  echo Set SST_WORKBENCH_ROOT or SST_PYTHON, or create a local .env from .env.example.
  set "_SST_ENV_FILE="
  set "_CAND="
  set "_NEXT="
  exit /b 1
)
set "_CAND=%_NEXT%"
goto :walk

:map_lane
if "%WB:~-1%"=="\" set "WB=%WB:~0,-1%"
if /I "%SST_GPU_LANE%"=="xpu" (
  set "SST_PYTHON=%WB%\.venv-a075-xpu\Scripts\python.exe"
  goto :verify
)
if /I "%SST_GPU_LANE%"=="cuda" (
  set "SST_PYTHON=%WB%\.venv-sst-cuda126\Scripts\python.exe"
  goto :verify
)
echo ERROR: Unknown SST_GPU_LANE="%SST_GPU_LANE%" ^(use xpu or cuda^)
set "_SST_ENV_FILE="
set "_CAND="
set "_NEXT="
set "WB="
exit /b 1

:verify
if not exist "%SST_PYTHON%" (
  echo ERROR: Python not found: "%SST_PYTHON%"
  echo Set SST_PYTHON to an existing python.exe, or install .venv-a075-xpu / .venv-sst-cuda126 under the workbench root.
  set "_SST_ENV_FILE="
  set "_CAND="
  set "_NEXT="
  set "WB="
  exit /b 1
)
set "_SST_ENV_FILE="
set "_CAND="
set "_NEXT="
set "WB="
exit /b 0
