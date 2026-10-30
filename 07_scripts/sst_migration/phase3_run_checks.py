"""Capture exact bounded subprocess checks; a smoke requires successful tests."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
from preflight import ROOT, read
from phase3_prepare import OUT, FAMILY, create_json

PYTHON = Path.home() / 'AppData/Local/Python/pythoncore-3.14-64/python.exe'


def execute(label, args, timeout):
    log = OUT / (label + '.log')
    record = OUT / (label + '.json')
    if log.exists() or record.exists():
        raise FileExistsError('Check record exists; preserve it: ' + label)
    started = time.monotonic()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
    with log.open('x', encoding='utf-8') as stream:
        try:
            result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            code = result.returncode
        except subprocess.TimeoutExpired:
            code = 124
    create_json(record, {'command': [str(a) for a in args], 'cwd': str(ROOT), 'exit_code': code,
                        'timeout_seconds': timeout, 'duration_seconds': time.monotonic()-started, 'log': log.relative_to(ROOT).as_posix()})
    print(label + ': exit=' + str(code), flush=True)
    if code:
        print(log.read_text(encoding='utf-8')[-5000:])
        raise SystemExit(code)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['tests', 'smoke'])
    args = p.parse_args()
    target = FAMILY / 'A011-v0.4.0'
    if args.stage == 'tests':
        q = read(OUT / 'framework_source_qualification.json')
        f = ROOT / q['selected_source']
        script = 'import sys,pytest;sys.path.insert(0,sys.argv[1]);raise SystemExit(pytest.main(sys.argv[2:]))'
        execute('framework_targeted_tests', [PYTHON, '-B', '-c', script, f, '-p', 'no:cacheprovider', '-q', '-rA', f/'tests/test_full_diagnostic_110.py', f/'tests/test_gates.py', f/'tests/test_protocol.py'], 120)
        execute('a011_tests', [PYTHON, '-B', target/'run_tests_v040.py'], 180)
    else:
        for label in ['framework_targeted_tests', 'a011_tests']:
            if read(OUT / (label + '.json'))['exit_code'] != 0:
                raise RuntimeError('Tests must pass before smoke')
        execute('a011_geometry_smoke', [PYTHON, '-B', target/'run_framework_smoke.py'], 120)


if __name__ == '__main__':
    main()
