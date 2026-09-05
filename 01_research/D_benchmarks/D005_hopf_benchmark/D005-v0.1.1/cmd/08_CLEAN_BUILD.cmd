@echo off
setlocal
cd /d "%~dp0\.."
echo [SST-HOPF] Removing native build artifacts and result folders...
if exist build rmdir /s /q build
for %%F in (sst_hopf_native\_native*.pyd sst_hopf_native\_native*.so) do del /q "%%F" 2>nul
if exist results rmdir /s /q results
echo [SST-HOPF] Clean complete. .venv preserved.
exit /b 0
