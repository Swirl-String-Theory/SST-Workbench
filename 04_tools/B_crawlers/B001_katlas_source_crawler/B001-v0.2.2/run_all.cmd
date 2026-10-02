@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo ============================================================
echo SST Katlas Source Crawler v0.2.2 - FULL ONE-CLICK
echo Output: Katlas_Sources_v0.2.2_Outputs
echo RDF + knots + links + curated page enrichment
echo ============================================================
call run_all_rdf_only.cmd || exit /b 1
echo [4/5] Fetching curated raw pages + rendered HTML and enriching JSON...
.venv\Scripts\python.exe -m katlas_source.cli --config config.json fetch-profile sst_curated || exit /b 1
echo [5/5] Strict final validation against source RDF...
.venv\Scripts\python.exe -m katlas_source.cli --config config.json validate || exit /b 1
echo ============================================================
echo DONE
echo Output folder:
echo %~dp0..\Katlas_Sources_v0.2.2_Outputs
echo ============================================================
