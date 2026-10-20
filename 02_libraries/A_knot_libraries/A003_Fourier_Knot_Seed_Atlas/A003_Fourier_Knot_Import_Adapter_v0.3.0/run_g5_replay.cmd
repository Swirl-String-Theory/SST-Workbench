@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
python "%HERE%replay_g5_v024.py"
exit /b %errorlevel%
