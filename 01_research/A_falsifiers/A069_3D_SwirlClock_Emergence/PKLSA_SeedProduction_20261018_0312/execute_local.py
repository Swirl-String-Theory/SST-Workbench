from pathlib import Path
import subprocess, sys, json, hashlib, os, time

ROOT=Path(r'C:\workspace\projects\SST-Workbench')
RUN=Path(__file__).resolve().parent
PKG=RUN/'PKLSA_KnotPlot_SeedProduction_v0.1.0'
EXE=Path(r'C:\Users\oscar\AppData\Local\Programs\KnotPlot\KnotPlot.exe')
LOG=RUN/'logs'; LOG.mkdir(exist_ok=True)
os.environ['PYTHONDONTWRITEBYTECODE']='1'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def snapshot():
    result={}
    for top in ['01_research','03_data']:
        for base,dirs,files in os.walk(ROOT/top):
            dirs[:]=[d for d in dirs if d not in ['.git','__pycache__','.venv']]
            for name in files:
                p=Path(base)/name
                try:
                    s=p.stat(); result[str(p.relative_to(ROOT))]=[s.st_size,s.st_mtime_ns]
                except OSError: pass
    return result
def call(name,args,cwd=PKG,env=None):
    with (LOG/(name+'.log')).open('wb') as f:
        try: c=subprocess.run(args,cwd=cwd,stdout=f,stderr=subprocess.STDOUT,timeout=60,env=env); rc=c.returncode
        except subprocess.TimeoutExpired: rc='TIMEOUT'
    records.append(dict(name=name,args=[str(x) for x in args],cwd=str(cwd),exit_code=rc))
    (RUN/'commands.json').write_text(json.dumps(records,indent=2))
    print(name,rc,flush=True)
    return rc
records=[]
before=snapshot(); (RUN/'protected_metadata_before.json').write_text(json.dumps(before,sort_keys=True))
protected=ROOT/'01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas/E010-v0.3.1'
hashes={str(p.relative_to(ROOT)):sha(p) for p in protected.rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','.venv','build'])}
(RUN/'E010_hashes_before.json').write_text(json.dumps(hashes,indent=2))
(RUN/'git_status_before.txt').write_bytes(subprocess.check_output(['git','status','--porcelain=v1','-uall'],cwd=ROOT))
(RUN/'environment.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'knotplot':str(EXE),'knotplot_sha256':sha(EXE),'package_sha256':sha(RUN/'package.zip'),'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
call('regression',[sys.executable,'-m','unittest','discover','-s','tests','-v'])
call('generation',[sys.executable,'src/seedproduction.py','--out','production_out'])
call('legacy_inventory',[sys.executable,'src/audit_legacy.py',str(ROOT/'03_data/A_knots/04_knotplot/final'),'--csv',str(RUN/'legacy_quarantine_inventory.csv')])
out=PKG/'production_out'
probe=out/'runtime_probe.kpc'; probe.write_text('reset all\nversion\nparameters\nquit\n')
call('runtime_probe',[str(EXE),'-stdin','-nographics'],out) if False else None
with probe.open('rb') as inp,(LOG/'runtime_probe.log').open('wb') as log:
    try: cp=subprocess.run([str(EXE),'-stdin','-nographics'],cwd=out,stdin=inp,stdout=log,stderr=subprocess.STDOUT,timeout=30); rc=cp.returncode
    except subprocess.TimeoutExpired: rc='TIMEOUT'
records.append({'name':'runtime_probe','exit_code':rc})
for script in sorted((out/'kpc_diagnostic').glob('*.kpc')):
    # Preserve supplied script; append only an explicit process exit in a separate wrapper.
    wrapper=out/(script.stem+'__local.kpc');wrapper.write_bytes(script.read_bytes()+b'quit\n')
    with wrapper.open('rb') as inp,(LOG/(script.stem+'.log')).open('wb') as log:
        try: cp=subprocess.run([str(EXE),'-stdin','-nographics'],cwd=out,stdin=inp,stdout=log,stderr=subprocess.STDOUT,timeout=30); rc=cp.returncode
        except subprocess.TimeoutExpired: rc='TIMEOUT'
    records.append({'name':script.stem,'exit_code':rc})
    readback=out/'checkpoints'/(script.stem+'_roundtrip.txt')
    if readback.exists(): call('roundtrip_'+script.stem,[sys.executable,'src/check_knotplot_roundtrip.py',str(out/'geometry'/(script.stem+'.txt')),str(readback)])
    else: print('MISSING READBACK',script.stem,flush=True)
after=snapshot()
changes=[k for k in before.keys()|after.keys() if before.get(k)!=after.get(k)]
hash_changes=[k for k,v in hashes.items() if not (ROOT/k).is_file() or sha(ROOT/k)!=v]
(RUN/'preservation.json').write_text(json.dumps({'metadata_files_checked':len(before),'research_data_metadata_changes':changes,'E010_files_hashed':len(hashes),'E010_hash_changes':hash_changes},indent=2))
(RUN/'commands.json').write_text(json.dumps(records,indent=2))
print('PRESERVATION',len(changes),len(hash_changes),flush=True)

