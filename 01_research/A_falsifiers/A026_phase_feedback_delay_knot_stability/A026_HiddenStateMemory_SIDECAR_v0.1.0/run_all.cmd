@echo off
setlocal
cd /d "%~dp0"
if "%~1"=="" goto BASIC
if /I "%~1"=="TEST" goto TEST
if /I "%~1"=="BASIC" goto BASIC
if /I "%~1"=="EULER" goto EULER
if /I "%~1"=="FULL" goto FULL
 echo Usage: run_all.cmd TEST^|BASIC^|EULER "input.npz"^|FULL "input.npz"
 exit /b 2
:TEST
python run_falsifier.py TEST
exit /b %errorlevel%
:BASIC
python run_falsifier.py BASIC
exit /b %errorlevel%
:EULER
if "%~2"=="" (echo Missing NPZ input & exit /b 2)
python run_falsifier.py EULER --input "%~2"
exit /b %errorlevel%
:FULL
if "%~2"=="" (echo Missing native Euler input; refusing fake FULL & exit /b 3)
python run_falsifier.py FULL --input "%~2"
exit /b %errorlevel%
