"""Fail-closed A077-v0.1.1 G5/pybind11 flat-vector interface repair.

This is intentionally an instance-owned source hotfix with an external
provenance sidecar, *not* a modification of Framework v1.1.0 or frozen theory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

PATCH_DIR = Path(__file__).resolve().parent
EXPECTED_OLD = "f94cc2fbc39ed5021949328844cbee5fc1a6a950c775c05ddbb8fe3812c1640a"
NEW_PIPE = "fefca6e8fd1ac5319df1b180c626325faab211920a1ef79663c4d104e46ffb9a"
NEW_TEST = "02171d5c2cc802651bd979e81622bd73c9c026ea6cd71d660dc69415fc43df2a"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--target', type=Path, default=Path.cwd())
    ap.add_argument('--check', action='store_true', help='Verify only; do not write')
    args = ap.parse_args()
    root = args.target.resolve()
    if root.name != 'A077-v0.1.1' or not (root/'framework_bootstrap.py').is_file():
        raise SystemExit('[PATCH][REFUSED] target must be the root of A077-v0.1.1')
    pipeline = root/'experiment'/'pipeline.py'
    test = root/'tests'/'test_g5_native_shape_p1.py'
    sources = {'pipeline': PATCH_DIR/'experiment'/'pipeline.py',
               'test': PATCH_DIR/'tests'/'test_g5_native_shape_p1.py'}
    for key,expected in (('pipeline',NEW_PIPE),('test',NEW_TEST)):
        if sha(sources[key]) != expected:
            raise SystemExit(f'[PATCH][REFUSED] patch payload hash incorrect: {key}')
    if not pipeline.is_file():
        raise SystemExit('[PATCH][REFUSED] existing experiment/pipeline.py is missing')
    actual = sha(pipeline)
    if actual not in (EXPECTED_OLD, NEW_PIPE):
        raise SystemExit('[PATCH][REFUSED] existing pipeline.py was modified: '+actual)
    if test.exists() and sha(test) != NEW_TEST:
        raise SystemExit('[PATCH][REFUSED] conflicting existing regression test')
    if not (root/'_sst_runtime'/'sst_falsifier'/'outputs.py').is_file():
        raise SystemExit('[PATCH][REFUSED] Framework runtime incomplete')
    if actual == NEW_PIPE and test.is_file() and sha(test) == NEW_TEST:
        print('[PATCH][PASS] already applied; both patch payload hashes verified')
        return
    if args.check:
        print('[PATCH][PASS] target and source verified; safe to apply (no changes made)')
        return
    # Keep the original version and all run outputs: only two instance-owned files change.
    # External backups and patch sidecars are deliberately *outside* the frozen source tree.
    backup_base = root.parent / 'A077-v0.1.1_PATCH_BACKUPS'
    backup_base.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup_dir = backup_base / ('G5_p1_' + stamp)
    backup_dir.mkdir(exist_ok=False)
    backup = backup_dir/'pipeline.py.before'
    shutil.copyfile(pipeline, backup)
    if sha(backup) != actual:
        raise SystemExit('[PATCH][REFUSED] could not verify backup integrity')
    if actual != NEW_PIPE:
        tmp = pipeline.with_name('pipeline.py.A077_G5_p1_TMP')
        with tmp.open('xb') as f:
            f.write(sources['pipeline'].read_bytes())
        if sha(tmp) != NEW_PIPE:
            raise SystemExit('[PATCH][REFUSED] temporary pipeline hash incorrect')
        os.replace(tmp, pipeline)
    if not test.exists():
        with test.open('xb') as f:
            f.write(sources['test'].read_bytes())
    if sha(pipeline) != NEW_PIPE or sha(test) != NEW_TEST:
        raise SystemExit('[PATCH][REFUSED] post-write validation failed')
    record = {
        'schema':'A077-G5-NATIVE-SHAPE-HOTFIX-1',
        'target':str(root),
        'phase':'DEVELOPMENT_SOURCE_HOTFIX_NOT_SCIENTIFIC_PROMOTION',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'experiment_pipeline_sha256_before':actual,
        'experiment_pipeline_sha256_after':NEW_PIPE,
        'tests_sha256':NEW_TEST,
        'backup_path':str(backup),
        'changes':["reshape native std::vector<double> time-major output to Python (steps+1,2*rings) matrix",
                   'reject wrong length, shape and nonfinite output',
                   'add four pure interface regression tests'],
        'unchanged':['falsifier.toml','preregistration/FROZEN_PROTOCOL.json',
                     'science_contract.json','gate_plan.json','report/FALSIFIER_REPORT.tex',
                     '_sst_runtime/**','native/**','configs/**'],
        'warning': 'Code has changed after previous FREEZE. Treat existing run IDs as historical; maintain this sidecar and issue a fresh reproducible version for scientific publication.'
    }
    (backup_dir/'PATCH_PROVENANCE.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('[PATCH][RESTORED] experiment/pipeline.py  SHA256='+NEW_PIPE)
    print('[PATCH][ADDED] tests/test_g5_native_shape_p1.py  SHA256='+NEW_TEST)
    print('[PATCH][AUDIT] '+str(backup_dir/'PATCH_PROVENANCE.json'))
    print('[PATCH][PASS] source and regression test validated; rerun project tests and BACKEND_PREFLIGHT, FREEZE, BASIC, FULL, CERTIFY')

if __name__=='__main__':
    main()
