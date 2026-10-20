@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "HERE=%~dp0"
set "ATLAS=%HERE%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS=%SST_ATLAS_ROOT%"
set "FRAMEWORK=%SST_FRAMEWORK_ROOT%"
if not defined FRAMEWORK (
  for %%I in ("%HERE%..\..\..\..") do set "FRAMEWORK=%%~fI\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
)
if not exist "%FRAMEWORK%\RELEASE_INFO.json" (
  echo FAIL_CLOSED: Missing v1.0.10 Framework. Set SST_FRAMEWORK_ROOT. 1>&2
  exit /b 4
)
if not exist "%ATLAS%\manifest.json" (
  echo FAIL_CLOSED: Missing A003-v0.1.2 manifest. Set SST_ATLAS_ROOT. 1>&2
  exit /b 4
)
python "%HERE%g5_qualification_v028.py" --atlas "%ATLAS%" --framework-root "%FRAMEWORK%" --out-root "%HERE%..\A003_Fourier_Knot_Import_Adapter_v0.3.0-outputs" %*
set "RC=%ERRORLEVEL%"
echo A003 v0.3.0 qualified screen: rc=%RC%; 0=bounded PASS, 2=scientific FAIL, 3=UNRESOLVED, 4=integrity/runtime FATAL.
exit /b %RC%
