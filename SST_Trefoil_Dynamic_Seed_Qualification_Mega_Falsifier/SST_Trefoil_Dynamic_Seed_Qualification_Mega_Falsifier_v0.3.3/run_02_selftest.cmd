@echo off
setlocal
cd /d "%~dp0"
call _common.cmd
"%PY%" -m sst_seed_falsifier.selftest
"%PY%" -m pytest -q tests
