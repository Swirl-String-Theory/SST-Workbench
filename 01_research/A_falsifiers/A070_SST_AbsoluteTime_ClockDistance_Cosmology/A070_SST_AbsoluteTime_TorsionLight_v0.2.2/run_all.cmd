@echo off
setlocal
py run_all.py %*
exit /b %errorlevel%
