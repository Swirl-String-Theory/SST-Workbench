@echo off
setlocal
cd /d "%~dp0"
python tools\verify_atlas.py
set ERR=%ERRORLEVEL%
if not exist families\ (
  echo GEOMETRY_MISSING: families/ absent ? see GEOMETRY_RESTORE.md
  exit /b 2
)
exit /b %ERR%
