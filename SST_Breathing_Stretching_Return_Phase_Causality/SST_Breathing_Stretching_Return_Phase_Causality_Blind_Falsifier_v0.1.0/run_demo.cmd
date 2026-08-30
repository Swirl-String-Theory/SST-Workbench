@echo off
setlocal
call .venv\Scripts\activate.bat
python -m sst_bsrp_falsifier.selftest
