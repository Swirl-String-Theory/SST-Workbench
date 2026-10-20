@echo off
setlocal EnableExtensions
set "ADAPTER_ROOT=%~dp0"
set "ATLAS_ROOT=%ADAPTER_ROOT%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS_ROOT=%SST_ATLAS_ROOT%"
set "WORKBENCH_ROOT=C:\workspace\projects\SST-Workbench"
if defined SST_WORKBENCH_ROOT set "WORKBENCH_ROOT=%SST_WORKBENCH_ROOT%"
set "FRAMEWORK_ROOT=%WORKBENCH_ROOT%\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
if defined SST_FRAMEWORK_ROOT set "FRAMEWORK_ROOT=%SST_FRAMEWORK_ROOT%"
if not exist "%FRAMEWORK_ROOT%\sst_falsifier\gates.py" (
 echo G6 BLOCKED: missing exact framework v1.0.10; set SST_FRAMEWORK_ROOT. 1>&2
 exit /b 4
)
set "SST_FRAMEWORK_ROOT=%FRAMEWORK_ROOT%"
python "%ADAPTER_ROOT%g6_pklsa_pilot_v029.py" --atlas "%ATLAS_ROOT%" --workbench "%WORKBENCH_ROOT%" --framework-root "%FRAMEWORK_ROOT%" %*
exit /b %ERRORLEVEL%
