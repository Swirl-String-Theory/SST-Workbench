@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
python "%HERE%g5_provider_smoketest.py"
exit /b %errorlevel%
