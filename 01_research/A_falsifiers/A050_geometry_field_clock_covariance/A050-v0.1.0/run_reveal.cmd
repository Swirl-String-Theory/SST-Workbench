@echo off
setlocal
set "OUT=SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs"
call .venv\Scripts\activate.bat
python reveal\interpret.py "%OUT%"
powershell -NoProfile -Command "Compress-Archive -Force -Path '%OUT%\*','reveal\MAPPING.md' -DestinationPath '..\SST_Geometry_Field_Clock_Covariance_Blind_Falsifier_v0.1.0-outputs_REVEALED.zip'"
endlocal
