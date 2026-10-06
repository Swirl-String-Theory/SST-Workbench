@echo off
call run_setup.cmd || exit /b 1
.venv\Scripts\python.exe setup.py build_ext --inplace
