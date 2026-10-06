@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_00_install.cmd || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli selftest --force-python || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli blind --config configs/ci.json --force-python --overwrite || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli seal --config configs/ci.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli reveal --config configs/ci.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli package --config configs/ci.json || exit /b 1
echo A055 v0.1.1 CI diagnostic complete. Do not use CI outputs as scientific results.
