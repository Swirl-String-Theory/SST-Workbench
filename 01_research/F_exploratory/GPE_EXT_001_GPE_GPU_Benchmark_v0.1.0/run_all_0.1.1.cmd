@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if "%~1"=="" (set "MODE=BASIC") else (set "MODE=%~1")
if /I "%MODE%"=="ALL" set "MODE=FULL"
if /I "%MODE%"=="SETUP" goto SETUP
if /I "%MODE%"=="DATA" goto FETCH_ONLY
if /I "%MODE%"=="SELFTEST" goto SELFTEST
if /I "%MODE%"=="FREEZE" goto FREEZE
if /I "%MODE%"=="REVEAL" goto RUN_ONLY
if /I "%MODE%"=="REPORT_ONLY" goto RUN_ONLY
if /I not "%MODE%"=="BASIC" if /I not "%MODE%"=="FULL" (
  echo Usage: run_all.cmd [BASIC^|FULL^|ALL^|DATA^|SETUP^|SELFTEST^|FREEZE^|REPORT_ONLY^|REVEAL]
  exit /b 2
)
call :ensure_env || exit /b 1
call :fetch
if errorlevel 1 echo [GPE] WARNING: research data absent/invalid; CPU and GPU diagnostic gates will still run.
if not exist "preregistration\FROZEN_PROTOCOL.json" (
  echo [GPE] First run: freezing completed scientific protocol...
  "%PY%" run_instance.py FREEZE || exit /b 1
)
"%PY%" run_instance.py %MODE%
exit /b %errorlevel%
:SETUP
call :ensure_env
exit /b %errorlevel%
:FETCH_ONLY
py -3 -m experiment.fetch_data --dest data\external
exit /b %errorlevel%
:SELFTEST
call :ensure_env || exit /b 1
"%PY%" -m unittest discover -s tests -p test_*.py -v
exit /b %errorlevel%
:FREEZE
call :ensure_env || exit /b 1
"%PY%" run_instance.py FREEZE
exit /b %errorlevel%
:RUN_ONLY
if not exist ".venv\Scripts\python.exe" (echo Run BASIC first to initialize environment & exit /b 4)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" run_instance.py %MODE%
exit /b %errorlevel%
:ensure_env
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv 2>nul || py -3 -m venv .venv || (echo [ERROR] Python 3.11+ required & exit /b 10)
)
set "PY=%CD%\.venv\Scripts\python.exe"
"%PY%" -m pip install --disable-pip-version-check -q -r requirements_gpe.txt || exit /b 1
"%PY%" -c "import torch; assert hasattr(torch, 'xpu') and torch.xpu.is_available()" >nul 2>nul
if errorlevel 1 (
  echo [GPE] Installing PyTorch with Intel XPU support - large download, Arc compute driver required.
  "%PY%" -m pip install --disable-pip-version-check --upgrade --force-reinstall torch --index-url https://download.pytorch.org/whl/xpu
  if errorlevel 1 echo [GPE] WARNING: XPU wheel setup failed. G6 will be NOT_RUN_PREREQUISITE, not PASS.
)
"%PY%" -c "import torch; print('Torch:',torch.__version__); print('XPU:',torch.xpu.is_available() if hasattr(torch,'xpu') else False)"
exit /b 0
:fetch
"%PY%" -m experiment.fetch_data --dest data\external
exit /b %errorlevel%
