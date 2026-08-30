@echo off
setlocal
cd /d "%~dp0"
call run_sweep.cmd --qhp-min=42.0586,1.43298,6.215 --qhp-max=44.3970,1.47040,6.320 --qhp-mode=line --scripts=20 --max-ago=100000 --knots=3.1 --name=K31_qhp_100k
exit /b %ERRORLEVEL%
