@echo off
setlocal
cd /d "%~dp0"
call run_00_install.cmd || exit /b 1
call run_05_build_cpp.cmd || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli selftest || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli blind --config configs/ci.json --overwrite || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli seal --config configs/ci.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli reveal --config configs/ci.json || exit /b 1
.venv\Scripts\python.exe -m a055_spectrum.cli package --config configs/ci.json || exit /b 1
