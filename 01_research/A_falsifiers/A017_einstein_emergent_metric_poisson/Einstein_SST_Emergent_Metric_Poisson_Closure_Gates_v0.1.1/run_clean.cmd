@echo off
setlocal
cd /d "%~dp0"
if exist build rmdir /s /q build
for /d /r %%D in (__pycache__) do @if exist "%%D" rmdir /s /q "%%D"
del /s /q src\einstein_sst_gates\_fast*.pyd 2>nul
echo [SST] Build artifacts cleaned. .venv and outputs preserved.
