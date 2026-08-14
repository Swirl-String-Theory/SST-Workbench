from __future__ import annotations
import argparse,csv,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from native_ext import backend_info
from helmholtz_sst.io import load_centerline,sha256_file,atomic_json
from helmholtz_sst.geometry import resample_closed,thickness_proxy,geom_stats,closure_edge_ratio
from helmholtz_sst.metrics import total_velocity,total_energy_length,relative_equilibrium,orientation_symmetry,mirror_symmetry,holonomy_metrics
from helmholtz_sst.blind import blind_id
from helmholtz_sst.gates import evaluate

def discover(root,cfg):
    files=[]
    for pat in cfg.get('include',[]):
        if any(ch in pat for ch in '*?[]'):files+=list(root.glob(pat))
        else:
            p=root/pat
            if p.exists():files.append(p)
    if not files:files=list(root.glob(cfg.get('fallback_glob','*.txt')))
    # Avoid obvious non-geometry metadata text files.
    files=[p for p in files if p.is_file() and not p.name.lower().startswith(('readme','manifest'))]
    uniq=[];seen=set()
    for p in sorted(files,key=lambda x:x.name.lower()):
        rp=str(p.resolve())
        if rp not in seen:uniq.append(p);seen.add(rp)
    m=int(cfg.get('max_files',0));return uniq[:m] if m>0 else uniq

def compute_sample(path,cfg,pre,threads):
    fhash=sha256_file(path);bid=blind_id(fhash,pre['blind_id_salt']);raw=load_centerline(path)
    n=int(cfg['resample_n']);n2=int(cfg['convergence_n']);nt=int(cfg.get('thickness_n',n2));
    comps=[resample_closed(p,n) for p in raw];comps2=[resample_closed(p,n2) for p in raw];compt=[resample_closed(p,nt) for p in raw]
    gs,L=geom_stats(comps);closure=[closure_edge_ratio(p) for p in raw];tp=thickness_proxy(compt,threads);th=float(tp['thickness_proxy']);a=float(cfg.get('core_radius_scale',1.0))*th
    if not np.isfinite(a) or a<=0:raise ValueError('non-positive thickness/core radius proxy')
    v=total_velocity(comps,a,'softcore',threads);req=relative_equilibrium(comps,v);el=total_energy_length(comps,a,threads)
    v2=total_velocity(comps2,a,'softcore',threads);req2=relative_equilibrium(comps2,v2);el2=total_energy_length(comps2,a,threads)
    conv={'energy_rel_diff':float(abs(el2-el)/max(abs(el2),1e-300)),'re_abs_diff':float(abs(req2['normal_nrmse']-req['normal_nrmse'])),'energy_length_low':float(el),'energy_length_high':float(el2),'re_low':req['normal_nrmse'],'re_high':req2['normal_nrmse']}
    nh=max(int(pre['diagnostics'].get('holonomy_source_min_n',384)),int(pre['diagnostics'].get('holonomy_source_factor',4))*n);comph=[resample_closed(p,nh) for p in raw]
    hol=holonomy_metrics(comph,th,pre['diagnostics']['holonomy_stations_per_component'],pre['diagnostics']['holonomy_loop_points'],pre['diagnostics']['holonomy_loop_radius_as_thickness'],threads)
    sym={'orientation_relative_error':orientation_symmetry(comps,a,'softcore',threads),'mirror_relative_error':mirror_symmetry(comps,a,'softcore',threads)}
    edge_mean=float(np.mean([g['edge_mean'] for g in gs]));gates,overall=evaluate(gs,closure,th,edge_mean,conv,hol,req,sym,pre)
    sweep=[]
    for m in pre['diagnostics']['core_radius_sweep_multipliers']:
        aa=a*float(m);vv=total_velocity(comps,aa,'softcore',threads);rr=relative_equilibrium(comps,vv);ee=total_energy_length(comps,aa,threads);sweep.append({'multiplier':m,'core_radius':aa,'re_normal_nrmse':rr['normal_nrmse'],'energy_length':ee})
    return bid,{'blind_id':bid,'input_sha256':fhash,'overall_status':overall,'gates':gates,'diagnostics':{'n_components':len(comps),'length_reference':L,'core_radius_reference':a,'thickness_proxy':th,'thickness_details':tp,'energy_length_reference':el,'relative_equilibrium':req,'convergence':conv,'holonomy_rows':hol,'symmetry':sym,'core_radius_sweep':sweep},'static_dataset_guard':pre['static_dataset_guard']}

def main():
    ap=argparse.ArgumentParser(description='Target-blind Helmholtz-SST relaxed-knot campaign');ap.add_argument('--knots-dir',type=Path,required=True);ap.add_argument('--config',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--threads',type=int,default=0);ap.add_argument('--require-native',action='store_true');ap.add_argument('--strict-exit',action='store_true');a=ap.parse_args()
    cfg=json.loads(a.config.read_text());pre_path=ROOT/cfg['preregister'];pre=json.loads(pre_path.read_text());bi=backend_info(force_build=False)
    if a.require_native and not bi['native_available']:print('[ERROR] native backend required but unavailable',file=sys.stderr);return 4
    files=discover(a.knots_dir,cfg)
    if not files:print('[ERROR] no knot centerline files discovered',file=sys.stderr);return 4
    a.out.mkdir(parents=True,exist_ok=True);(a.out/'private').mkdir(exist_ok=True);samples=[];mapping=[];errors=[]
    for i,p in enumerate(files,1):
        try:
            bid,s=compute_sample(p,cfg,pre,a.threads);samples.append(s);mapping.append({'blind_id':bid,'filename':p.name,'absolute_path':str(p.resolve()),'input_sha256':s['input_sha256']});print(f'[{i}/{len(files)}] {bid}: {s["overall_status"]}')
            if cfg.get('write_per_sample_json',True):atomic_json(a.out/f'{bid}.json',s)
        except Exception as e:
            fh=sha256_file(p);bid=blind_id(fh,pre['blind_id_salt']);errors.append({'blind_id':bid,'error_type':type(e).__name__,'error':str(e)});mapping.append({'blind_id':bid,'filename':p.name,'absolute_path':str(p.resolve()),'input_sha256':fh});print(f'[{i}/{len(files)}] {bid}: PIPELINE_ERROR {type(e).__name__}')
    counts={k:sum(s['overall_status']==k for s in samples) for k in ['PASS_CANDIDATE','FALSIFIED_RELATIVE_EQUILIBRIUM','INCONCLUSIVE_NUMERICS','INVALID_GEOMETRY']}
    frozen={'protocol':pre['protocol'],'version':pre['version'],'mode':cfg['mode'],'backend':bi,'threads':a.threads,'config_sha256':sha256_file(a.config),'preregister_sha256':sha256_file(pre_path),'blindness':pre['blindness'],'n_inputs':len(files),'n_completed':len(samples),'n_errors':len(errors),'counts':counts,'samples':samples,'errors':errors}
    fp=a.out/'frozen_result.json';atomic_json(fp,frozen);digest=sha256_file(fp);(a.out/'frozen_result.json.sha256').write_text(digest+'  frozen_result.json\n',encoding='ascii');atomic_json(a.out/'private/reveal_map.json',{'warning':'DO NOT INSPECT BEFORE FREEZE','mapping':mapping});atomic_json(a.out/'summary.json',{'mode':cfg['mode'],'backend':bi,'n_inputs':len(files),'n_completed':len(samples),'n_errors':len(errors),'counts':counts,'frozen_sha256':digest,'reveal_command':f'run_04_reveal.cmd {fp}'})
    print(json.dumps({'output':str(a.out),'counts':counts,'errors':len(errors),'frozen_sha256':digest},indent=2))
    if errors:return 4
    if a.strict_exit and (counts['FALSIFIED_RELATIVE_EQUILIBRIUM'] or counts['INCONCLUSIVE_NUMERICS'] or counts['INVALID_GEOMETRY']):return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
