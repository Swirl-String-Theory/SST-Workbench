from __future__ import annotations
import argparse, json, os, platform, sys, time
from datetime import datetime
from pathlib import Path
import numpy as np
from .geometry_track import run_geometry, analyze_geometry
from .knot_io import list_knot_files, load_geometry
from .native import backend_status, biot_savart_velocity, python_biot_savart_velocity
from .reduced_momentum import run_reduced_momentum
from .storage import run_storage
from .freeze import freeze_outputs, verify_frozen
from .blind import unblind_report

ROOT=Path(__file__).resolve().parents[2]

def _cfg(profile_or_path:str)->tuple[Path,dict]:
    p=Path(profile_or_path)
    if not p.exists():
        p=ROOT/'config'/f'{profile_or_path}.json'
    if not p.exists(): raise FileNotFoundError(f'config/profile not found: {profile_or_path}')
    return p,json.loads(p.read_text(encoding='utf-8'))

def _auto_out(prefix):
    return ROOT/'outputs'/f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def _threads(v):
    if v is not None: return int(v)
    if os.environ.get('SST_NATIVE_THREADS'): return int(os.environ['SST_NATIVE_THREADS'])
    return min(16,os.cpu_count() or 1)

def cmd_preflight(a):
    cp,cfg=_cfg(a.profile); knots=Path(a.knots).resolve(); files=list_knot_files(knots,cfg)
    b=backend_status(force_build=a.force_build,verbose=a.verbose)
    rows=[]
    for p in files:
        g=load_geometry(p); m=g.metrics
        rows.append({'file':p.name,'components':len(g.components),'vertices':sum(len(c) for c in g.components),'residual':m.get('residual'),'edge_ratio':m.get('edge_length_ratio'),'thickness':m.get('thickness'),'ropelength':m.get('ropelength')})
    out={'version':'0.2.0','prefix':'3_','python':sys.version,'platform':platform.platform(),'config':str(cp),'knots_dir':str(knots),'selected_files':len(files),'backend':b,'threads':_threads(a.threads),'files':rows}
    print(json.dumps(out,indent=2)); return 0 if files else 2

def cmd_run(a):
    cp,cfg=_cfg(a.profile); knots=Path(a.knots).resolve(); out=Path(a.outdir).resolve() if a.outdir else _auto_out(cfg.get('profile','run'))
    out.mkdir(parents=True,exist_ok=True)
    (out/'preregister_frozen.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    tracks={}
    geo=run_geometry(knots,out,cfg,threads=_threads(a.threads),force_python=a.force_python,force_build=a.force_build)
    tracks['geometry']=geo
    if a.reduced_momentum:
        tracks['reduced_momentum']=run_reduced_momentum(Path(a.reduced_momentum),out,cfg['reduced_momentum_track'],cfg['blindness'])
    if a.storage:
        tracks['storage_current']=run_storage(Path(a.storage),out,cfg['storage_current_track'])
    statuses=[v.get('status','INCONCLUSIVE') for v in tracks.values()]
    overall='FAIL' if 'FAIL' in statuses else ('INCONCLUSIVE' if 'INCONCLUSIVE' in statuses else 'PASS')
    report={'protocol_version':cfg['protocol_version'],'profile':cfg.get('profile'),'prefix':'3_','config':str(cp),'knots_dir':str(knots),'blindness':cfg['blindness'],'overall_status':overall,'tracks':tracks,'external_tracks_present':{'reduced_momentum':bool(a.reduced_momentum),'storage_current':bool(a.storage)},'decision_rule':cfg['decision_rule']}
    (out/'blind_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    frozen=freeze_outputs(out)
    print(json.dumps({'overall_status':overall,'outdir':str(out),'frozen_files':len(frozen['files']),'geometry_backend':geo.get('runtime',{}).get('backend')},indent=2))
    return 1 if overall=='FAIL' else 0

def cmd_benchmark(a):
    cp,cfg=_cfg(a.profile); knots=Path(a.knots).resolve(); files=list_knot_files(knots,cfg)
    if not files: raise RuntimeError('no input files')
    p=files[0]
    tiny=json.loads(json.dumps(cfg)); tiny['geometry'].update({'resample_points_per_component':120,'stations_per_component':4,'radial_samples':2,'angular_samples':8})
    t=time.perf_counter(); py=analyze_geometry(p,tiny,threads=1,force_python=True); tpy=time.perf_counter()-t
    b=backend_status(force_build=True,verbose=a.verbose)
    result={'file':p.name,'python_elapsed_s':tpy,'native':b}
    if b.get('native_available'):
        t=time.perf_counter(); cpp=analyze_geometry(p,tiny,threads=_threads(a.threads),force_python=False); tcpp=time.perf_counter()-t
        result.update({'cpp_elapsed_s':tcpp,'speedup':tpy/max(tcpp,1e-12),'C_python':py.median_C_blind,'C_cpp':cpp.median_C_blind,'C_relative_difference':abs(py.median_C_blind-cpp.median_C_blind)/max(abs(py.median_C_blind),1e-300)})
    print(json.dumps(result,indent=2)); return 0

def cmd_selftest(a):
    rng=np.random.default_rng(123); samples=rng.normal(size=(16,3)); a0=rng.normal(size=(20,3)); b0=a0+0.05*rng.normal(size=(20,3))
    ref=python_biot_savart_velocity(samples,a0,b0,1.0,0.2)
    got,info=biot_savart_velocity(samples,a0,b0,1.0,0.2,threads=_threads(a.threads),force_python=not a.native,force_build=a.native)
    rel=float(np.linalg.norm(ref-got)/max(np.linalg.norm(ref),1e-300)); ok=rel<1e-11
    print(json.dumps({'ok':ok,'relative_error':rel,'backend':info},indent=2)); return 0 if ok else 1

def cmd_freeze(a):
    out=Path(a.outdir).resolve(); print(json.dumps(freeze_outputs(out),indent=2)); return 0

def cmd_verify(a):
    print(json.dumps(verify_frozen(Path(a.outdir).resolve()),indent=2)); return 0

def cmd_unblind(a):
    br=Path(a.blind_report).resolve(); out=Path(a.out).resolve() if a.out else br.parent/'results_unblinded.json'
    r=unblind_report(br,Path(a.commitments).resolve(),Path(a.key).resolve(),out); print(json.dumps(r,indent=2)); return 0

def build_parser():
    p=argparse.ArgumentParser(prog='sst-maxwell3',description='Prefix 3 Maxwell Physical Lines blind falsifier v0.2.0')
    s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('preflight'); q.add_argument('--profile',default='basic'); q.add_argument('--knots',default=r'..\..\KnotPlot\knots\final'); q.add_argument('--threads',type=int); q.add_argument('--force-build',action='store_true'); q.add_argument('--verbose',action='store_true'); q.set_defaults(func=cmd_preflight)
    q=s.add_parser('run'); q.add_argument('--profile',default='basic'); q.add_argument('--knots',default=r'..\..\KnotPlot\knots\final'); q.add_argument('--threads',type=int); q.add_argument('--outdir'); q.add_argument('--force-python',action='store_true'); q.add_argument('--force-build',action='store_true'); q.add_argument('--reduced-momentum'); q.add_argument('--storage'); q.set_defaults(func=cmd_run)
    q=s.add_parser('benchmark'); q.add_argument('--profile',default='basic'); q.add_argument('--knots',default=r'..\..\KnotPlot\knots\final'); q.add_argument('--threads',type=int); q.add_argument('--verbose',action='store_true'); q.set_defaults(func=cmd_benchmark)
    q=s.add_parser('selftest'); q.add_argument('--threads',type=int); q.add_argument('--native',action='store_true'); q.set_defaults(func=cmd_selftest)
    q=s.add_parser('freeze'); q.add_argument('--outdir',required=True); q.set_defaults(func=cmd_freeze)
    q=s.add_parser('verify-frozen'); q.add_argument('--outdir',required=True); q.set_defaults(func=cmd_verify)
    q=s.add_parser('unblind'); q.add_argument('--blind-report',required=True); q.add_argument('--commitments',default=str(ROOT/'blind'/'commitments.json')); q.add_argument('--key',required=True); q.add_argument('--out'); q.set_defaults(func=cmd_unblind)
    return p

def main(argv=None):
    a=build_parser().parse_args(argv)
    try: return a.func(a)
    except Exception as exc:
        print(f'[3_MAXWELL] ERROR: {exc}',file=sys.stderr)
        if os.environ.get('SST_TRACEBACK')=='1': raise
        return 2
if __name__=='__main__': raise SystemExit(main())
