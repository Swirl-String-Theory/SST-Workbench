@echo off
setlocal
call run_setup.cmd || exit /b 1
call run_build_native.cmd || exit /b 1
call .venv\Scripts\activate.bat
if exist demo_qhp rmdir /s /q demo_qhp
python -m sst_qhp_falsifier.cli demo demo_qhp || exit /b 1
call run_basic.cmd demo_qhp outputs\demo
