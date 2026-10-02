from __future__ import annotations
import argparse,json,os,platform,sys,time
from datetime import datetime
from pathlib import Path
import numpy as np

from .pklsa_adapter import PKLSARepository
from .topology_track import run_topology
from .pklsa_stress import run_pklsa_stress
from .native import backend_status,biot_savart_velocity,python_biot_savart_velocity,circulation_from_centerlines
from .reduced_momentum import run_reduced_momentum
from .storage import run_storage
from .freeze import freeze_outputs,verify_frozen
from .blind import unblind_report

ROOT=Path(__file__).resolve().parents[2]

def _cfg(profile_or_path):
    p=Path(profile_or_path)
    if not p.exists(): p=ROOT/'config'/f'{profile_or_path}.json'
    if not p.exists(): raise FileNotFoundError(f'config/profile not found: {profile_or_path}')
    return p,json.loads(p.read_text(encoding='utf-8'))

def _auto_out(prefix): return ROOT/'3_Maxwell_SST_Physical_Lines_Falsifier_v0.3.0-outputs'/f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
def _threads(v): return int(v if v is not None else os.environ.get('SST_NATIVE_THREADS',min(16,os.cpu_count() or 1)))

def _repo(a): return PKLSARepository.open(a.workbench,a.pklsa_release)

def cmd_preflight(a):
    cp,cfg=_cfg(a.profile); repo=_repo(a); b=backend_status(force_build=a.force_build,verbose=a.verbose)
    carriers,admission=repo.discover(cfg['pklsa_admission'],cfg['selection'].get('topology_include') or None,int(cfg['selection'].get('max_topologies',0)),int(cfg['selection'].get('max_carriers_per_topology',0)))
    sample=[]
    for c in carriers[:min(10,len(carriers))]:
        sample.append(c.blind_summary())
    out={'protocol_version':'0.3.0','prefix':'3_','python':sys.version,'platform':platform.platform(),'config':str(cp),'workbench':str(repo.workbench),'pklsa_release':str(repo.release_root),'pklsa_release_checks':repo.release_checks(),'admission':{k:v for k,v in admission.items() if k!='rejected'},'blind_sample':sample,'native_backend':b,'pklsa_exact_linking_native_available':repo.native is not None,'threads':_threads(a.threads)}
    print(json.dumps(out,indent=2)); return 0 if carriers and admission['release']['pass'] else 2

def cmd_run(a):
    cp,cfg=_cfg(a.profile); repo=_repo(a); out=Path(a.outdir).resolve() if a.outdir else _auto_out(cfg.get('profile','run'))
    out.mkdir(parents=True,exist_ok=True)
    (out/'preregister_frozen.json').write_text(json.dumps(cfg,indent=2),encoding='utf-8')
    provenance={'protocol_version':'0.3.0','prefix':'3_','pklsa_version':repo.release_meta.get('e010_version'),'pklsa_release_checks':repo.release_checks(),'workbench_root_hash':__import__('hashlib').sha256(str(repo.workbench).encode()).hexdigest(),'pklsa_release_root_hash':__import__('hashlib').sha256(str(repo.release_root).encode()).hexdigest()}
    (out/'upstream_provenance_blind.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    threads=_threads(a.threads)
    topo=run_topology(repo,out,cfg,threads=threads,force_python=a.force_python)
    carriers,_=repo.discover(cfg['pklsa_admission'],cfg['selection'].get('topology_include') or None,int(cfg['selection'].get('max_topologies',0)),int(cfg['selection'].get('max_carriers_per_topology',0)))
    stress=run_pklsa_stress(repo,carriers,out,cfg,threads=threads,force_python=a.force_python)
    tracks={'M1_M3_pklsa_stress':stress,'M6_M7_topology':topo}
    if a.reduced_momentum: tracks['M4_reduced_momentum']=run_reduced_momentum(Path(a.reduced_momentum),out,cfg['reduced_momentum_track'],cfg['blindness'])
    if a.storage: tracks['M5_storage_current']=run_storage(Path(a.storage),out,cfg['storage_current_track'])
    mandatory=[topo.get('status','INCONCLUSIVE'),stress.get('status','INCONCLUSIVE')]
    overall='FAIL' if 'FAIL' in mandatory else ('INCONCLUSIVE' if 'INCONCLUSIVE' in mandatory else 'PASS')
    report={'protocol_version':'0.3.0','profile':cfg.get('profile'),'prefix':'3_','blindness':cfg['blindness'],'overall_status':overall,'tracks':tracks,'external_tracks_present':{'reduced_momentum':bool(a.reduced_momentum),'storage_current':bool(a.storage)},'decision_rule':cfg['decision_rule']}
    (out/'blind_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    frozen=freeze_outputs(out)
    print(json.dumps({'overall_status':overall,'outdir':str(out),'frozen_files':len(frozen['files']),'pklsa_version':repo.release_meta.get('e010_version'),'native_backend':backend_status(False,False)},indent=2))
    return 1 if overall=='FAIL' else 0

def cmd_benchmark(a):
    n=280; t=np.linspace(0,2*np.pi,n,endpoint=False); source=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    s=np.linspace(0,2*np.pi,220,endpoint=False); probe=np.c_[1+.35*np.cos(s),np.zeros_like(s),.35*np.sin(s)]
    t0=time.perf_counter(); qpy,_=circulation_from_centerlines([source],probe,1.0,0.0,1,True); py=time.perf_counter()-t0
    b=backend_status(force_build=True,verbose=a.verbose); result={'python_elapsed_s':py,'python_circulation':qpy,'native':b}
    if b.get('native_available'):
        t0=time.perf_counter(); qcpp,_=circulation_from_centerlines([source],probe,1.0,0.0,_threads(a.threads),False); cpp=time.perf_counter()-t0
        result.update({'cpp_elapsed_s':cpp,'cpp_circulation':qcpp,'speedup':py/max(cpp,1e-12),'relative_difference':abs(qcpp-qpy)/max(abs(qpy),1e-300)})
    print(json.dumps(result,indent=2)); return 0

def cmd_selftest(a):
    rng=np.random.default_rng(123); samples=rng.normal(size=(16,3)); aa=rng.normal(size=(20,3)); bb=aa+.05*rng.normal(size=(20,3))
    ref=python_biot_savart_velocity(samples,aa,bb,1.0,.2); got,info=biot_savart_velocity(samples,aa,bb,1.0,.2,threads=_threads(a.threads),force_python=not a.native,force_build=a.native)
    rel=float(np.linalg.norm(ref-got)/max(np.linalg.norm(ref),1e-300));
    t=np.linspace(0,2*np.pi,256,endpoint=False); source=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]; s=np.linspace(0,2*np.pi,256,endpoint=False); probe=np.c_[1+.35*np.cos(s),np.zeros_like(s),.35*np.sin(s)]
    q,_=circulation_from_centerlines([source],probe,1.0,0.0,_threads(a.threads),force_python=not a.native)
    ok=rel<1e-11 and abs(abs(q)-1)<0.08
    print(json.dumps({'ok':ok,'velocity_relative_error':rel,'hopf_abs_circulation':abs(q),'backend':info},indent=2)); return 0 if ok else 1

def cmd_verify(a): print(json.dumps(verify_frozen(Path(a.outdir).resolve()),indent=2)); return 0
def cmd_unblind(a):
    br=Path(a.blind_report).resolve(); out=Path(a.out).resolve() if a.out else br.parent/'results_unblinded.json'
    r=unblind_report(br,Path(a.commitments).resolve(),Path(a.key).resolve(),out); print(json.dumps(r,indent=2)); return 0

def _add_common(q):
    q.add_argument('--profile',default='basic'); q.add_argument('--workbench'); q.add_argument('--pklsa-release'); q.add_argument('--threads',type=int)

def build_parser():
    p=argparse.ArgumentParser(prog='sst-maxwell3',description='Prefix-3 Maxwell Physical Lines / PKLSA blind falsifier v0.3.0')
    s=p.add_subparsers(dest='cmd',required=True)
    q=s.add_parser('preflight'); _add_common(q); q.add_argument('--force-build',action='store_true'); q.add_argument('--verbose',action='store_true'); q.set_defaults(func=cmd_preflight)
    q=s.add_parser('run'); _add_common(q); q.add_argument('--outdir'); q.add_argument('--force-python',action='store_true'); q.add_argument('--reduced-momentum'); q.add_argument('--storage'); q.set_defaults(func=cmd_run)
    q=s.add_parser('benchmark'); q.add_argument('--threads',type=int); q.add_argument('--verbose',action='store_true'); q.set_defaults(func=cmd_benchmark)
    q=s.add_parser('selftest'); q.add_argument('--threads',type=int); q.add_argument('--native',action='store_true'); q.set_defaults(func=cmd_selftest)
    q=s.add_parser('verify-frozen'); q.add_argument('--outdir',required=True); q.set_defaults(func=cmd_verify)
    q=s.add_parser('unblind'); q.add_argument('--blind-report',required=True); q.add_argument('--commitments',default=str(ROOT/'blind'/'commitments.json')); q.add_argument('--key',required=True); q.add_argument('--out'); q.set_defaults(func=cmd_unblind)
    return p

def main(argv=None):
    a=build_parser().parse_args(argv)
    try:return a.func(a)
    except Exception as exc:
        print(f'[3_MAXWELL] ERROR: {exc}',file=sys.stderr)
        if os.environ.get('SST_TRACEBACK')=='1': raise
        return 2
if __name__=='__main__': raise SystemExit(main())
