@echo off
setlocal
call _common.cmd
call .venv\Scripts\activate.bat
python -c "from sst_seed_falsifier.selftest import run; raise SystemExit(run(True))" || exit /b 1
pytest -q || exit /b 1
