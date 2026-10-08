from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, os, subprocess, time

ROOT=Path(__file__).resolve().parents[1]

def _sha256(path:Path, block=1024*1024):
    h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b=f.read(block)
            if not b: break
            h.update(b)
    return h.hexdigest()

def _workbench_root():
    for key in ('SST_WORKBENCH','SST_WORKBENCH_ROOT'):
        raw=os.environ.get(key,'').strip()
        if raw:
            return Path(os.path.expandvars(raw)).expanduser().resolve(), key
    # Installed canonical path: <WB>/01_research/A_falsifiers/.../A058-vX.Y.Z
    for p in [ROOT,*ROOT.parents]:
        if (p/'04_tools'/'A_geometry').is_dir() and (p/'01_research').is_dir():
            return p.resolve(), 'inferred_from_instance'
    return None, None

def _resolve_exe(explicit:str|None):
    if explicit and explicit.strip():
        return Path(os.path.expandvars(explicit)).expanduser().resolve(), 'argument'
    env=os.environ.get('KNOTPLOT_EXE','').strip()
    if env:
        return Path(os.path.expandvars(env)).expanduser().resolve(), 'KNOTPLOT_EXE'
    # User shortcut supplied for A058 uses USER_PROFILE; Windows normally defines USERPROFILE.
    for key in ('USER_PROFILE','USERPROFILE'):
        profile=os.environ.get(key,'').strip()
        if profile:
            p=Path(profile)/'AppData'/'Local'/'Programs'/'KnotPlot'/'KnotPlot.exe'
            if p.exists(): return p.resolve(), f'{key}_default'
    return None, 'not_found'

def _output_workdir():
    # Start-In may safely be the falsifier output directory because generated .kpc files use
    # absolute paths for campaign/results. This directory is runtime-only.
    out=ROOT.parent/'A058_KnotPlot_Parameter_Sensitivity_Relaxation_Robustness_Falsifier_v0.1.2-outputs'
    out.mkdir(parents=True,exist_ok=True)
    return out.resolve(), 'instance_outputs'

def _resolve_workdir(explicit:str|None):
    raw=(explicit or '').strip()
    if not raw:
        raw=os.environ.get('KNOTPLOT_STARTIN','').strip()
        if raw:
            p=Path(os.path.expandvars(raw)).expanduser().resolve()
            return p, 'KNOTPLOT_STARTIN'
        wb,source=_workbench_root()
        if wb is not None:
            p=wb/'04_tools'/'A_geometry'/'A001_knotplot'
            if p.is_dir(): return p.resolve(), f'{source}:04_tools/A_geometry/A001_knotplot'
        return _output_workdir()
    if raw.lower() in {'output','outputs'}:
        return _output_workdir()
    return Path(os.path.expandvars(raw)).expanduser().resolve(), 'argument'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--tier',choices=['smoke','pilot','full'],default='pilot')
    ap.add_argument('--exe',default='')
    ap.add_argument('--workdir',default='')
    ap.add_argument('--resume',action='store_true')
    a=ap.parse_args()
    mf=ROOT/'campaign'/f'manifest_{a.tier}.json'
    if not mf.exists(): raise SystemExit(f'Missing {mf}; run generate_campaign.py first')
    man=json.loads(mf.read_text(encoding='utf-8'))
    (ROOT/'campaign'/'active_tier.json').write_text(json.dumps({'tier':a.tier},indent=2)+'\n',encoding='utf-8')

    exe,exe_source=_resolve_exe(a.exe)
    if exe is None or not exe.is_file():
        raise SystemExit('KnotPlot executable not found. Checked --exe, KNOTPLOT_EXE, '
                         '%USER_PROFILE%\\AppData\\Local\\Programs\\KnotPlot\\KnotPlot.exe, '
                         'and %USERPROFILE%\\AppData\\Local\\Programs\\KnotPlot\\KnotPlot.exe.')
    workdir,workdir_source=_resolve_workdir(a.workdir)
    if not workdir.is_dir():
        raise SystemExit(f'KnotPlot Start In directory not found: {workdir}')

    runtime={
        'schema':'A058-KNOTPLOT-RUNTIME-1', 'tier':a.tier,
        'executable':str(exe), 'executable_source':exe_source,
        'executable_sha256':_sha256(exe), 'executable_bytes':exe.stat().st_size,
        'working_directory':str(workdir), 'working_directory_source':workdir_source,
        'sst_workbench':os.environ.get('SST_WORKBENCH',''),
        'sst_workbench_root':os.environ.get('SST_WORKBENCH_ROOT',''),
        'note':'Shortcut reference: target %USER_PROFILE%/AppData/Local/Programs/KnotPlot/KnotPlot.exe; Start In %SST_WORKBENCH%/04_tools/A_geometry/A001_knotplot/.',
    }
    (ROOT/'campaign'/f'runtime_{a.tier}.json').write_text(json.dumps(runtime,indent=2)+'\n',encoding='utf-8')
    print(f'KnotPlot : {exe} [{exe_source}]')
    print(f'Start In : {workdir} [{workdir_source}]')

    runlog=[]
    for i,c in enumerate(man['conditions'],1):
        cid=c['condition_id']; metrics=ROOT/'campaign'/'results'/cid/'metrics.csv'; metrics.parent.mkdir(parents=True,exist_ok=True)
        if a.resume and metrics.exists() and metrics.stat().st_size>0:
            print(f'[{i}/{len(man["conditions"])}] {cid} SKIP'); continue
        script=ROOT/c['script']; log=ROOT/'campaign'/'logs'/f'{cid}.log'; log.parent.mkdir(parents=True,exist_ok=True)
        print(f'[{i}/{len(man["conditions"])}] {cid} {c["topology_id"]} {c["label"]}')
        t=time.time()
        with script.open('rb') as inp, log.open('wb') as out:
            p=subprocess.run([str(exe),'-stdin','-nographics'],cwd=workdir,stdin=inp,stdout=out,stderr=subprocess.STDOUT)
        runlog.append({'condition_id':cid,'returncode':p.returncode,'seconds':time.time()-t,'metrics_exists':metrics.exists(),'working_directory':str(workdir)})
    (ROOT/'campaign'/f'runlog_{a.tier}.json').write_text(json.dumps(runlog,indent=2)+'\n',encoding='utf-8')
    bad=[r for r in runlog if r['returncode']!=0]
    print(f'Complete: {len(runlog)} executed, {len(bad)} nonzero exits')
    raise SystemExit(1 if bad else 0)
if __name__=='__main__': main()
