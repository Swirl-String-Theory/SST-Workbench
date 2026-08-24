@echo off
setlocal EnableExtensions
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe call run_install.cmd
if errorlevel 1 exit /b 1
.venv\Scripts\python.exe examples\generate_demo_dataset.py
.venv\Scripts\python.exe run_pipeline.py --profile basic --dataset examples\demo_knots --backend python
exit /b %errorlevel%
