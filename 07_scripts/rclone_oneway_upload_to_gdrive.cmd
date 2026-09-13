@echo off
setlocal EnableExtensions
rem One-way: local -> Google Drive only (never download / never delete local).
rem Uses rclone sync so remote matches local (remote-only extras removed).
rem Heavy many-file trees are uploaded as zips under 03_data/_rclone_bundles/
rem (build with 07_scripts/build_rclone_bundles.ps1). Raw trees are excluded.
rem
rem Policy: keep C:\workspace\projects\SST-Workbench OUT of Drive desktop Mirror.

set "SRC=C:\workspace\projects\SST-Workbench"
set "DST=gdrive:SST-Workbench"
set "RCLONE="
where rclone >nul 2>&1 && set "RCLONE=rclone"
if not defined RCLONE if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\rclone.exe" set "RCLONE=%LOCALAPPDATA%\Microsoft\WinGet\Links\rclone.exe"
if not defined RCLONE if exist "%ProgramFiles%\rclone\rclone.exe" set "RCLONE=%ProgramFiles%\rclone\rclone.exe"
if not defined RCLONE (
  echo ERROR: rclone not found on PATH
  exit /b 2
)

echo [oneway] SRC=%SRC%
echo [oneway] DST=%DST%
echo [oneway] mode=sync + zip bundles (local source of truth)
echo.

"%RCLONE%" sync "%SRC%" "%DST%" ^
  --progress ^
  --checkers 8 ^
  --transfers 4 ^
  --retries 20 ^
  --retries-sleep 10s ^
  --low-level-retries 30 ^
  --timeout 10m ^
  --contimeout 60s ^
  --drive-chunk-size 64M ^
  --drive-pacer-min-sleep 10ms ^
  --fast-list ^
  --delete-excluded ^
  --exclude ".git/**" ^
  --exclude "**/.git/**" ^
  --exclude ".tmp.driveupload/**" ^
  --exclude "**/.tmp.driveupload/**" ^
  --exclude "**/__pycache__/**" ^
  --exclude "**/.pytest_cache/**" ^
  --exclude "**/.idea/**" ^
  --exclude "**/node_modules/**" ^
  --exclude "**/.venv/**" ^
  --exclude "**/venv/**" ^
  --exclude "**/*.pyd" ^
  --exclude "**/*.pyc" ^
  --exclude "SST_Hopf_Benchmark/**" ^
  --exclude "03_data/A_knots/04_knotplot/knot_*/**" ^
  --exclude "03_data/A_knots/04_knotplot/final/**" ^
  --exclude "03_data/D_generated/knotplot_campaign_outputs/**" ^
  --exclude "03_data/D_generated/qhp/**" ^
  --exclude "03_data/D_generated/trefoil_closure/**" ^
  --exclude "03_data/D_generated/figures/**" ^
  --exclude "03_data/D_generated/3d/**" ^
  --exclude "03_data/D_generated/D001_3d_exports/**" ^
  --exclude "03_data/D_generated/vortexlab_spec_clock_runs/**" ^
  --exclude "03_data/D_generated/legacy_resources_swirl_results/**" ^
  --exclude "03_data/D_generated/legacy_dataset_exports/**" ^
  --exclude "03_data/D_generated/research_outputs/**" ^
  --exclude "03_data/D_generated/knotplot_reference/**" ^
  --exclude "09_archive/restore/**" ^
  --exclude "09_archive/trefoil_closure/**" ^
  %*

set RC=%ERRORLEVEL%
echo.
echo [oneway] done rc=%RC%
exit /b %RC%
