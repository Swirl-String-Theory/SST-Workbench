@echo off
setlocal
call .venv\Scripts\activate.bat || exit /b 1
python tools\pack_outputs.py A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0-outputs --prefix A056_PKLSA_Spectral_SineGordon_MittagLeffler_Falsifier_v0.1.0 || exit /b 1
