@echo off
setlocal
cd /d "%~dp0"
call run_sweep.cmd --qhp-min=42.0586,1.43298,6.215 --qhp-max=44.3970,1.47040,6.320 --qhp-mode=line --scripts=20 --max-ago=100000 --knots=3.1,5.1,7.1 --links=6.3.3,6.3.1 --torus=3.3,3.6,3.9,6.9,6.15,6.21 --beads-per-component=300 --name=MultiTopology_qhp_100k
exit /b %ERRORLEVEL%
