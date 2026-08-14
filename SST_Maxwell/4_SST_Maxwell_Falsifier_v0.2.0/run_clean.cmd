@echo off
setlocal
cd /d "%~dp0"
for /d %%D in (4_outputs_*) do rd /s /q "%%D"
if exist build rd /s /q build
for %%F in (native_ext\_native*.pyd native_ext\_native*.so) do del /q "%%F" 2>nul
echo [4_SST] Outputs/build artifacts removed. .venv preserved.
