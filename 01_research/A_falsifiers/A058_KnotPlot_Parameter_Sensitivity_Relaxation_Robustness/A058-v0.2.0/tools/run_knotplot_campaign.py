\
from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,os,subprocess,time
ROOT=Path(__file__).resolve().parents[1]
def _sha256(path:Path):
    h=hashlib.sha256();
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
def resolve_exe(explicit=''):
    if explicit.strip(): return Path(os.path.expandvars(explicit)).expanduser().resolve(),'argument'
    if os.environ.get('KNOTPLOT_EXE','').strip(): return Path(os.path.expandvars(os.environ['KNOTPLOT_EXE'])).expanduser().resolve(),'KNOTPLOT_EXE'
    for key in ('USER_PROFILE','USERPROFILE'):
        raw=os.environ.get(key,'').strip()
        if raw:
            p=Path(raw)/'AppData'/'Local'/'Programs'/'KnotPlot'/'KnotPlot.exe'
            if p.is_file(): return p.resolve(),f'{key}_default'
    return None,'not_found'
def workbench_root():
    for key in ('SST_WORKBENCH','SST_WORKBENCH_ROOT'):
        raw=os.environ.get(key,'').strip()
        if raw:return Path(os.path.expandvars(raw)).expanduser().resolve(),key
    for p in [ROOT,*ROOT.parents]:
        if (p/'04_tools'/'A_geometry').is_dir() and (p/'01_research').is_dir(): return p.resolve(),'inferred_from_instance'
    return None,None
def resolve_workdir(explicit=''):
    raw=explicit.strip() or os.environ.get('KNOTPLOT_STARTIN','').strip()
    if raw.lower() in {'output','outputs'}:
        out=ROOT/'A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.2.0-outputs'; out.mkdir(exist_ok=True)
        return out.resolve(),'instance_outputs'
    if raw:return Path(os.path.expandvars(raw)).expanduser().resolve(),'argument_or_env'
    wb,src=workbench_root()
    if wb:
        p=wb/'04_tools'/'A_geometry'/'A001_knotplot'
        if p.is_dir(): return p.resolve(),f'{src}:04_tools/A_geometry/A001_knotplot'
    out=ROOT/f'A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.2.0-outputs'; out.mkdir(exist_ok=True)
    return out.resolve(),'instance_outputs'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--tier',choices=['pilot'],default='pilot'); ap.add_argument('--exe',default=''); ap.add_argument('--workdir',default=''); ap.add_argument('--resume',action='store_true'); a=ap.parse_args()
    man=json.loads((ROOT/'campaign/manifest_pilot.json').read_text(encoding='utf-8'))
    exe,es=resolve_exe(a.exe); wd,ws=resolve_workdir(a.workdir)
    if exe is None or not exe.is_file(): raise SystemExit('KnotPlot executable not found.')
    if not wd.is_dir(): raise SystemExit(f'KnotPlot Start In directory not found: {wd}')
    runtime={'schema':'A058-KNOTPLOT-RUNTIME-2','tier':'pilot','executable':str(exe),'executable_source':es,'executable_sha256':_sha256(exe),'executable_bytes':exe.stat().st_size,'working_directory':str(wd),'working_directory_source':ws}
    (ROOT/'campaign/runtime_pilot.json').write_text(json.dumps(runtime,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    cps=json.loads((ROOT/'configs/default.json').read_text(encoding='utf-8'))['topology']['checkpoints']; final=f'i{int(cps[-1]):06d}.txt'; rows=[]
    for i,c in enumerate(man['conditions'],1):
        cid=c['condition_id']; rdir=ROOT/'campaign/results'/cid
        if a.resume and (rdir/final).is_file() and (rdir/final).stat().st_size>0:
            print(f'[{i}/101] {cid} SKIP'); continue
        sp=ROOT/c['script']; log=ROOT/'private/campaign_logs/pilot'/f'{cid}.log'; log.parent.mkdir(parents=True,exist_ok=True)
        print(f'[{i}/101] {cid} {c["axis_id"]} m={c["multiplier"]:.12g}')
        t=time.time()
        with sp.open('rb') as inp,log.open('wb') as out:
            p=subprocess.run([str(exe),'-stdin','-nographics'],cwd=wd,stdin=inp,stdout=out,stderr=subprocess.STDOUT)
        rows.append({'condition_id':cid,'returncode':p.returncode,'seconds':time.time()-t,'final_coordinate_exists':(rdir/final).is_file()})
    (ROOT/'campaign/runlog_pilot.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    bad=[x for x in rows if x['returncode']!=0]; print(f'Complete: {len(rows)} executed, {len(bad)} nonzero exits'); raise SystemExit(1 if bad else 0)
if __name__=='__main__':main()
