@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
"%PY%" setup_native.py build_ext --inplace
