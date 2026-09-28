"""Explicit run-scoped CLI. Every full invocation creates a new output tree."""
from pathlib import Path
import argparse
import json
import subprocess
import sys
from sst_torsion import pipeline
from sst_torsion.run_contract import package_run, seal_run, write_json

ROOT = Path(__file__).resolve().parent


def main(default_stage='all'):
    p = argparse.ArgumentParser()
    p.add_argument('--stage', default=default_stage, choices=['all','prepare','python','native','environment','record-native','parity','seal','reveal','package'])
    p.add_argument('--run-dir', type=Path)
    p.add_argument('--suite', default='qualification')
    p.add_argument('--python-only', action='store_true')
    a = p.parse_args()
    if a.stage in ('all','prepare'):
        if a.run_dir:
            p.error('prepare always creates a unique run; do not provide --run-dir')
        if not a.python_only and a.stage == 'all':
            import torsion_native  # fail before creating a partial run; build_native.cmd first
        run = pipeline.prepare(ROOT, a.suite)
        print(str(run), flush=True)
        if a.stage == 'prepare':
            return
        audit = run/'AUDIT'
        audit.mkdir()
        command = [sys.executable,'-m','pytest','-q','tests']
        if a.python_only:
            command += ['-k','not native']
        result = subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (audit/(run.name+'_tests.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        write_json(run/'BLIND'/'test_execution.json',{'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode:
            raise RuntimeError('tests failed; partial run retained without seal')
        pipeline.record_environment(run)
        pipeline.analyze(run,'python')
        if not a.python_only:
            pipeline.record_native(run)
            pipeline.analyze(run,'native')
            pipeline.parity(run)
        seal_run(run)
        report = pipeline.reveal(run)
        archives = package_run(run)
        print(json.dumps({'run_id':run.name,'report':report,'archives':archives},indent=2))
        if report['status'].endswith('FAILED'):
            raise SystemExit(1)
        return
    if a.run_dir is None:
        p.error('--run-dir is required for an individual stage')
    run=a.run_dir.resolve()
    operations = {'python':lambda:pipeline.analyze(run,'python'),
        'native':lambda:pipeline.analyze(run,'native'),'environment':lambda:pipeline.record_environment(run),
        'record-native':lambda:pipeline.record_native(run),'parity':lambda:pipeline.parity(run),
        'seal':lambda:seal_run(run),'reveal':lambda:pipeline.reveal(run),'package':lambda:package_run(run)}
    print(json.dumps(operations[a.stage](),indent=2))


if __name__=='__main__':
    main()
