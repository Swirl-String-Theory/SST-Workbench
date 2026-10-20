@echo off
setlocal EnableExtensions
set "HERE=%~dp0"
set "ATLAS=%HERE%..\A003-v0.1.2"
if defined SST_ATLAS_ROOT set "ATLAS=%SST_ATLAS_ROOT%"
set "FRAMEWORK=%SST_FRAMEWORK_ROOT%"
if not defined FRAMEWORK (
  for %%I in ("%HERE%..\..\..\..") do set "FRAMEWORK=%%~fI\06_templates\SST_Falsifier_Framework\SST_Falsifier_Framework_v1.0.10"
)
if not exist "%FRAMEWORK%\RELEASE_INFO.json" (
 echo FAIL_CLOSED: SST Framework v1.0.10 missing. Set SST_FRAMEWORK_ROOT. 1>&2
 exit /b 4
)
if not exist "%ATLAS%\manifest.json" (
 echo FAIL_CLOSED: A003-v0.1.2 atlas missing. 1>&2
 exit /b 4
)
python "%HERE%a003_diagnostic_v027.py" --atlas "%ATLAS%" --framework-root "%FRAMEWORK%" --out-root "%HERE%..\A003_Fourier_Knot_Import_Adapter_v0.2.7-outputs" %*
set "RC=%ERRORLEVEL%"
echo A003 v0.2.7 diagnostic completed; consult GATE_LEDGER.json and DIAGNOSTIC_RUN_SUMMARY.json.
echo Scientific FAIL is intentionally preserved as nonzero exit. Errorlevel=%RC%.
exit /b %RC%
