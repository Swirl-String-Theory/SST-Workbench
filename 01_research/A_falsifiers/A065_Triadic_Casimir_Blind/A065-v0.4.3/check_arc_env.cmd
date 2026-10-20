@echo off
setlocal
cd /d "%~dp0"
echo === Python interpreter used by A065 ===
if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else if defined VIRTUAL_ENV (
    set "PY=%VIRTUAL_ENV%\Scripts\python.exe"
) else (
    set "PY=python"
)
"%PY%" -c "import sys;print(sys.executable);print(sys.version)"
if errorlevel 1 exit /b 3
"%PY%" -c "import dpctl,dpnp;print('dpctl',dpctl.__version__);print('dpnp',dpnp.__version__);print([(d.name,str(d.backend)) for d in dpctl.get_devices()])"
if errorlevel 1 (
    echo Dependencies absent or incompatible in THIS interpreter.
    echo Install via: "%PY%" -m pip install -r requirements_arc_v041.txt
    exit /b 4
)
exit /b 0
