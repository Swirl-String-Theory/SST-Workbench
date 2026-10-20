@echo off
setlocal
pushd "%~dp0.."
py -3 "data\f005_data_pilot_v0.2.0.py" --root . --inspect-large --verify-small-md5
set rc=%ERRORLEVEL%
popd
exit /b %rc%
