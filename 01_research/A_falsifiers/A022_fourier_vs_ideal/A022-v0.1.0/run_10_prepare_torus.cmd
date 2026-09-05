@echo off
setlocal
cd /d "%~dp0"
call _common.cmd || exit /b 1
call config\paths.cmd
if exist blind_catalog rmdir /s /q blind_catalog
if exist private rmdir /s /q private
"%PY%" -m sst_fourier_ideal_falsifier.cli prepare --out . --base "%SST_FVI_BASE%" --ideal "%SST_FVI_IDEAL%" --ideal-js "%SST_FVI_IDEAL_JS%" --fseries-root "%SST_FVI_FSERIES%" --relaxed-root "%SST_FVI_RELAXED%" --mode torus --n 192
exit /b %errorlevel%
