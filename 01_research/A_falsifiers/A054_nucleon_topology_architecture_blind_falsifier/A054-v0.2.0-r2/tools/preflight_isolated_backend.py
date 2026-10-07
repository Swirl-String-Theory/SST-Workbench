from __future__ import annotations
from pathlib import Path
import subprocess, sys, tempfile, shutil, json

here=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='a054_isolated_preflight_') as td:
    camp=Path(td)/'campaign'
    cmd=[sys.executable, str(here/'tools'/'build_blind_runner.py'), '--campaign', str(camp), '--require-openmp']
    r=subprocess.run(cmd, cwd=str(here), text=True, capture_output=True)
    if r.stdout:
        print(r.stdout, end='')
    if r.returncode:
        if r.stderr:
            print(r.stderr, file=sys.stderr, end='')
        raise SystemExit(r.returncode)
    manifest=json.loads((camp/'blind_runner'/'RUNNER_MANIFEST.json').read_text(encoding='utf-8'))
    print('ISOLATED_PREFLIGHT', json.dumps({
        'python_executable': manifest.get('python_executable'),
        'native_source': manifest.get('native_source'),
        'native_destination': manifest.get('native_destination'),
        'native_probe_file': manifest.get('native_probe_file'),
        'native_import_verified': manifest.get('native_import_verified'),
        'native_openmp_verified': manifest.get('native_openmp_verified'),
    }, indent=2))
    if not manifest.get('native_import_verified') or not manifest.get('native_openmp_verified'):
        raise SystemExit(5)
