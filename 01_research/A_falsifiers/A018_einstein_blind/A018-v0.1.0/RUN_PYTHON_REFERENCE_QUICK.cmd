@echo off
setlocal EnableExtensions
cd /d "%~dp0"
call "%~dp0_common.cmd" || exit /b 1
"%PYTHON_EXE%" -m pip install -r requirements.txt || exit /b 1
"%PYTHON_EXE%" run_campaign.py --config configs\quick.json --input-root "%SST_KNOT_DIR%" --allow-python
exit /b %errorlevel%
