@echo off
setlocal
cd /d "%~dp0"
python reprocess_detector.py audit_fourier_quick_research --out-dir audit_fourier_quick_research_detector_v0.1.2.4 %*
exit /b %ERRORLEVEL%
