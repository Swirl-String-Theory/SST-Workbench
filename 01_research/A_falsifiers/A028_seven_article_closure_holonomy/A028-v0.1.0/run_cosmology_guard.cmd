@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call run_00_install.cmd || exit /b 1
set "CFG=%~1"
if "%CFG%"=="" set "CFG=examples\log_q_joint_article7.json"
.venv\Scripts\python.exe scripts\audit_log_q_model.py "%CFG%"
