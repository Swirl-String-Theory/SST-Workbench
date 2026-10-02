@echo off
setlocal
cd /d "%~dp0"
call run_fetch_qgi_public_pdf.cmd
if errorlevel 1 exit /b 1
call run_all.cmd
exit /b %errorlevel%
