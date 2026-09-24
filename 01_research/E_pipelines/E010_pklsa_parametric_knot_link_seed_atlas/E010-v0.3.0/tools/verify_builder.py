from __future__ import annotations
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
required=[
 'README.md','setup.py','pyproject.toml','requirements.txt',
 'configs/qualification_basic.json','configs/qualification_extended.json','configs/qualification_publication.json',
 'pklsa_builder/builder.py','pklsa_builder/qualification.py','pklsa_builder/repo_finder.py','pklsa_builder/source_discovery.py','cpp/pklsa_native.cpp',
 'data/SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json',
 'data/topology_sources/linkinfo_data_complete.xls','data/topology_sources/knotinfo_data_complete.xls.zip',
 'data/fixtures/knot.3_1.fseries','data/fixtures/Ideal.txt.gz','data/fixtures/3_1_katlas_braid.xyz',
 'run_repo_scan.cmd','run_repo_scan_deep.cmd',
]
missing=[x for x in required if not (ROOT/x).exists()]
if missing:
 print(json.dumps({'status':'FAIL','missing':missing},indent=2)); raise SystemExit(2)
cp=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(ROOT/'tests'),'-v'],cwd=ROOT)
if cp.returncode: raise SystemExit(cp.returncode)
cp2=subprocess.run([sys.executable,'-m','compileall','-q',str(ROOT/'pklsa_builder')],cwd=ROOT)
if cp2.returncode: raise SystemExit(cp2.returncode)
print(json.dumps({'status':'PASS','required_files':len(required),'builder_version':'0.2.0','builder_root':str(ROOT)},indent=2))
