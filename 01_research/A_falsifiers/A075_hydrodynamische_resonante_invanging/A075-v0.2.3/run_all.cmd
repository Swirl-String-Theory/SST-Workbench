@echo off
setlocal
cd /d "%~dp0"
if not defined SST_FALSIFIER_FRAMEWORK_ROOT set "SST_FALSIFIER_FRAMEWORK_ROOT=C:\workspace\projects\SST-Workbench\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
set "SST_WORKBENCH_ROOT=%CD%"
python run_instance.py %*
exit /b %errorlevel%
