@echo off
setlocal
set ENV=%~dp0.venv_a068_xpu
if not exist "%ENV%\Scripts\python.exe" (
 echo Missing separate XPU environment. To create, run SETUP_XPU_SEPARATE_ENV.cmd explicitly.
 exit /b 2
)
"%ENV%\Scripts\python.exe" "%~dp0diagnostics\xpu_probe.py"
exit /b %ERRORLEVEL%
