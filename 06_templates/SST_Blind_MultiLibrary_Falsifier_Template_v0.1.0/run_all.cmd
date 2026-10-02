@echo off
setlocal
call run_00_setup.cmd || exit /b 1
call run_01_selftest.cmd || exit /b 1
call run_02_example.cmd || exit /b 1
call .venv\Scripts\activate.bat
python tools\pack_outputs.py SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0-outputs ..\SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0-outputs_BLIND.zip || exit /b 1
echo PASS - template infrastructure completed.
