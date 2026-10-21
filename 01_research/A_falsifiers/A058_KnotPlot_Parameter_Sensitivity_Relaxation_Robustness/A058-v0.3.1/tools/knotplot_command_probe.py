"""Standalone, non-scientific KnotPlot command qualification.

Never touches A058's pre-registered seed, 271 conditions, private files or gate ledger.
KnotPlot input scripts originate in the user-provided knotplot.com/man command page.
"""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess
from pathlib import Path

METRICS_SCRIPT = '''reset all
load 3.1
version
length
rog
alex -1
data open A058_command_metrics.csv
data format "/N,/l,/g,/D,/I"
data header
data
data close
'''
HEDGEHOG_SCRIPT = '''reset all
hedgehog 108 1
length
rog
'''
SPOOL_SCRIPT = '''reset all
spool 108 2 1 0.5
length
rog
'''
ALIAS_SCRIPT = '''reset all
alias ~loadtrefoil "load 3.1;length;rog"
~loadtrefoil
'''
FRAME_SCRIPT = '''reset all
frame command "load 3.1"
frame 0
length
rog
'''
SCRIPTS = {
    'metrics': METRICS_SCRIPT,
    'hedgehog': HEDGEHOG_SCRIPT,
    'spool': SPOOL_SCRIPT,
    'alias': ALIAS_SCRIPT,
    'frame': FRAME_SCRIPT,
}

def generate(folder: Path) -> dict:
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if any(folder.iterdir()):
        raise FileExistsError('Probe output directory must be new/empty: '+str(folder))
    records={}
    for name,script in SCRIPTS.items():
        p=folder/(name+'.kpc');p.write_text(script,encoding='utf-8',newline='\n')
        records[name]={'script':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                       'interpretation':'standalone diagnostic; NOT A058 scientific acquisition'}
    (folder/'MANIFEST.json').write_text(json.dumps({'schema':'A058-KNOTPLOT-COMMAND-PROBES-1',
         'commands':records,'native_execution':'NOT_RUN','blind_protocol_unchanged':True},
        indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return records

def run_probe(executable: Path, workdir: Path, probe_dir: Path, timeout: int=60) -> dict:
    """Run ONLY pre-generated non-blind command scripts, and preserve raw logs locally.
    Every probe starts KnotPlot in a new process; rejects undocumented errors.
    """
    executable=Path(executable).resolve();workdir=Path(workdir).resolve();probe_dir=Path(probe_dir).resolve()
    if not executable.is_file():raise FileNotFoundError(executable)
    if not workdir.is_dir():raise NotADirectoryError(workdir)
    if (probe_dir/'RESULTS.json').exists():raise FileExistsError('Probe RESULTS.json already exists; do not overwrite')
    if (workdir/'A058_command_metrics.csv').exists():
        raise FileExistsError('Refusing to overwrite previous A058_command_metrics.csv in workdir')
    results={}
    for name in SCRIPTS:
        infile=probe_dir/(name+'.kpc');outfile=probe_dir/(name+'.log')
        if not infile.is_file():raise FileNotFoundError(infile)
        with infile.open('rb') as inp, outfile.open('wb') as out:
            try:
                cp=subprocess.run([str(executable),'-stdin','-nographics'],cwd=workdir,
                                  stdin=inp,stdout=out,stderr=subprocess.STDOUT,timeout=timeout,check=False)
                rc=cp.returncode
            except subprocess.TimeoutExpired:
                rc=None
        raw=outfile.read_text(encoding='utf-8',errors='replace')
        errors=[p for p in ('unknown command','freeglut  error:','freeglut error:') if p in raw.casefold()]
        status=('PASS_COMMAND_ACCEPTED' if rc==0 and not errors else
                'TIMEOUT' if rc is None else 'UNSUPPORTED_OR_FAILED')
        csv=workdir/'A058_command_metrics.csv'
        if name=='metrics':
            # Never treat a stale CSV as fresh (the user should pick an isolated
            # workdir or clear old generated files before running).
            status='NEEDS_CSV_CHECK' if status=='PASS_COMMAND_ACCEPTED' and not csv.exists() else status
        results[name]={'status':status,'returncode':rc,'errors':errors,'log_path':str(outfile),
                       'logs_may_contain_local_paths':True}
    doc={'schema':'A058-KNOTPLOT-COMMAND-PROBE-RESULT-1','native_execution':'ATTEMPTED',
         'scientific_inference':'NONE','results':results}
    (probe_dir/'RESULTS.json').write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return doc

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True,type=Path)
    ap.add_argument('--exe',type=Path);ap.add_argument('--workdir',type=Path)
    args=ap.parse_args()
    if bool(args.exe)!=bool(args.workdir):ap.error('--exe and --workdir must both be present to run native command probes')
    generate(args.out)
    if args.exe:
        report=run_probe(args.exe,args.workdir,args.out)
        print(json.dumps(report,indent=2))
    else:print('Scripts generated. Native execution NOT_RUN; supply --exe and --workdir to probe.')
if __name__=='__main__':main()
