@echo off
setlocal
rem OPTIONAL/EXPLICIT ONLY. Does not touch Workbench framework/A068 virtual env.
rem Requires separately installed Python 3.12 for confirmed PyTorch-XPU wheel availability.
set ENV=%~dp0.venv_a068_xpu
if exist "%ENV%" (
  echo Refusing to overwrite existing XPU environment: %ENV%
  exit /b 2
)
py -3.14 -m venv "%ENV%" || exit /b 1
"%ENV%\Scripts\python.exe" -m pip install --upgrade pip || exit /b 1
"%ENV%\Scripts\python.exe" -m pip install torch --index-url https://download.pytorch.org/whl/xpu || exit /b 1
"%ENV%\Scripts\python.exe" -m pip install numpy || exit /b 1
"%ENV%\Scripts\python.exe" "%~dp0diagnostics\xpu_probe.py"
exit /b %ERRORLEVEL%