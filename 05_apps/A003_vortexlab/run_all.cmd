@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>&1
if errorlevel 1 (
  echo ERROR: Node.js 20+ is nodig voor de VortexLab P2-kwalificatie.
  exit /b 1
)
call npm run check
if errorlevel 1 (
  echo FAIL: VortexLab-tests faalden. Wijzigingen zijn niet gekwalificeerd.
  exit /b 1
)
echo PASS: VortexLab P2 tests. Fysische Euler-sluiting blijft ONOPGELOST.
exit /b 0
