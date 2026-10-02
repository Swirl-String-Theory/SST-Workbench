@echo off
setlocal
python -m sst_counterpulley.build_ext_if_needed --force --strict
exit /b %errorlevel%
