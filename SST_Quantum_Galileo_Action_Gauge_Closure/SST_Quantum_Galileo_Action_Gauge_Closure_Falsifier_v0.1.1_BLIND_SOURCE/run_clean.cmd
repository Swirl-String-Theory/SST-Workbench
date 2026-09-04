@echo off
setlocal
cd /d "%~dp0"
if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat
set PYTHONPATH=%CD%
python -m sst_qgi.cli clean --config configs\basic.json
if exist build rmdir /s /q build
for %%F in (sst_qgi_native*.pyd sst_qgi_native*.so) do if exist "%%F" del /q "%%F"
echo Clean complete.
endlocal
