@echo off
setlocal EnableExtensions
if "%SST_WORKBENCH_ROOT%"=="" set "SST_WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
set "INST=%SST_WORKBENCH_ROOT%\01_research\F_exploratory\GPE_EXT_001_GPE_GPU_Benchmark_v0.1.1"
if not exist "%INST%\preflight_report.py" (
 echo ERROR: No installed GPE v0.1.1 instance found at "%INST%".
 exit /b 2
)
if exist "%INST%\preregistration\FROZEN_PROTOCOL.json" (
 echo ERROR: v0.1.1 protocol is frozen. Refusing to modify the instance.
 exit /b 3
)
py -3 "%~dp0apply_patch.py" "%INST%"
exit /b %errorlevel%
