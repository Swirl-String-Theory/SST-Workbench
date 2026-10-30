"""Independent heartbeat supervisor for long-running Windows falsifier commands.

A second Python process can print RUNNING heartbeats while a scientific C++ extension
holds the worker's Global Interpreter Lock (GIL). Exit code is propagated verbatim.
The transient stage status file is not a scientific artifact, and is removed on exit.
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def cadence_seconds():
    try:
        value=float(os.environ.get('SST_PROGRESS_HEARTBEAT_SECONDS','15'))
        return value if 0.02<=value<=3600 else 15.0
    except (TypeError,ValueError):
        return 15.0


def run_monitored(command, *, stream=None, env=None, cwd=None, cadence=None):
    output=stream if stream is not None else sys.stdout
    period=cadence if cadence is not None else cadence_seconds()
    if not (0.02<=period<=3600):raise ValueError('invalid heartbeat cadence')
    with tempfile.TemporaryDirectory(prefix='sst_progress_') as td:
        stage_file=Path(td)/'state.json'
        child_env=dict(os.environ if env is None else env)
        child_env['SST_PROGRESS_STATUS_FILE']=str(stage_file)
        child_env['SST_PROGRESS_SUPERVISED']='1'
        child_env['PYTHONUNBUFFERED']='1'
        t0=time.monotonic()
        # STDOUT/STDERR are inherited and visible immediately, not captured until exit.
        proc=subprocess.Popen(command,cwd=cwd,env=child_env)
        try:
            while True:
                try:
                    rc=proc.wait(timeout=period)
                    return rc
                except subprocess.TimeoutExpired:
                    phase='INITIALIZING';counter='';age=''
                    try:
                        data=json.loads(stage_file.read_text(encoding='utf-8'))
                        phase=str(data.get('phase','UNKNOWN'))[:64]
                        if isinstance(data.get('completed'),int) and isinstance(data.get('total'),int):
                            counter=f" {data['completed']}/{data['total']}"
                        age=f" latest_worker_checkpoint={data.get('elapsed_s','?')}s"
                    except (OSError,ValueError,TypeError):
                        pass
                    print(f"[SST][HEARTBEAT] RUNNING phase={phase}{counter} elapsed={time.monotonic()-t0:.1f}s{age}",file=output,flush=True)
        except KeyboardInterrupt:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill();proc.wait()
            return 130


if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'BASIC'
    raise SystemExit(run_monitored([sys.executable,'-u',str(ROOT/'run_instance.py'),mode],cwd=ROOT))
