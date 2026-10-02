@echo off
setlocal
python paper_upgrade\gate.py --selftest
if errorlevel 1 exit /b 1
echo [C006] paper-upgrade selftest PASS
