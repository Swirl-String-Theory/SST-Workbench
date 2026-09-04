@echo off
setlocal
python run_newton_krylov.py %*
exit /b %ERRORLEVEL%
