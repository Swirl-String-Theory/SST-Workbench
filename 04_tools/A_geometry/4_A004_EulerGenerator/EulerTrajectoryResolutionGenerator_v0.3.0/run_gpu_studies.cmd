@echo off
setlocal
cd /d "%~dp0"
call "%~dp0set_sst_python.cmd"
if errorlevel 1 exit /b %ERRORLEVEL%
"%SST_PYTHON%" -m resolver.gpu_studies %*
exit /b %ERRORLEVEL%
