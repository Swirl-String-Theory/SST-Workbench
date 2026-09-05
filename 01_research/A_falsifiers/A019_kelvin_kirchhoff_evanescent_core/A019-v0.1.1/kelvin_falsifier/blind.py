from __future__ import annotations
import hashlib, hmac, json, os, secrets, shutil, time
from pathlib import Path
from .io import write_json, sha256_file, read_json, read_components
from .geometry import estimate_thickness
from .dynamics import analyze_case


def _case_id(secret: bytes, digest: str, index: int):
    token=hmac.new(secret,f'{index}:{digest}'.encode(),hashlib.sha256).hexdigest()[:16].upper()
    return 'CASE_'+token


def prepare_blind(cases, out_root: str|Path, mode: str, cfg: dict, prereg_path: str|Path):
    root=Path(out_root); blind=root/'blind_campaign'; data=blind/'data'; results=blind/'results'
    data.mkdir(parents=True,exist_ok=True); results.mkdir(parents=True,exist_ok=True)
    secret=secrets.token_bytes(32); key={'mode':mode,'cases':{}}
    manifest={'mode':mode,'cases':[]}
    for i,c in enumerate(cases):
        cid=_case_id(secret,c['sha256'],i); dst=data/f'{cid}.txt'; shutil.copy2(c['path'],dst)
        # Only numerical metadata needed by the blind solver is retained; names/labels remain private.
        m={'case_id':cid,'path':str(dst.relative_to(blind)),'sha256':c['sha256'],'thickness':c['thickness'],'rr_residual':c['rr_residual'],'rr_edge_cv':c['rr_edge_cv'],'component_count':c['component_count'],'vertices_per_component':c['vertices_per_component']}
        manifest['cases'].append(m)
        key['cases'][cid]={'filename':c['filename'],'original_path':c['path'],'metrics_path':c['metrics_path'],'rr_ropelength':c['rr_ropelength'],'rr_length':c['rr_length']}
    write_json(blind/'blind_manifest.json',manifest)
    write_json(root/'private_blind_key.json',key)
    p=Path(prereg_path); frozen=results/'frozen_preregistration.json'; shutil.copy2(p,frozen)
    write_json(results/'frozen_preregistration.sha256.json',{'sha256':sha256_file(frozen),'source_name':p.name,'frozen_before_case_results':True})
    write_json(root/'campaign_config.json',cfg)
    return blind


def _sanitize_for_json(obj):
    import numpy as np
    if isinstance(obj,dict): return {k:_sanitize_for_json(v) for k,v in obj.items() if k!='_artifacts'}
    if isinstance(obj,list): return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj,tuple): return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj,np.ndarray): return obj.tolist()
    if isinstance(obj,(np.floating,np.integer)):
        x=obj.item()
        if isinstance(x,float) and not np.isfinite(x): return None
        return x
    if isinstance(obj,float) and not np.isfinite(obj): return None
    return obj


def run_blind(blind_dir: str|Path, cfg: dict, threads: int, require_native=True, force_python=False):
    blind=Path(blind_dir)
    if (blind/'private_blind_key.json').exists(): raise RuntimeError('Private mapping must not be inside blind campaign')
    manifest=read_json(blind/'blind_manifest.json'); results=blind/'results'; rows=[]
    for c in manifest['cases']:
        cid=c['case_id']; cdir=results/cid; cdir.mkdir(exist_ok=True)
        comps=read_components(blind/c['path'])
        core=c.get('thickness'); provenance='RIDGERUNNER_METRICS'
        if core is None or float(core)<=0:
            core=estimate_thickness(comps); provenance='NUMERICAL_FALLBACK_ESTIMATE'
        t0=time.time()
        try:
            res=analyze_case(comps,float(core),cfg,threads,require_native=require_native,force_python=force_python)
            res['case_id']=cid; res['input_sha256']=c['sha256']; res['original_points_per_component']=[len(x) for x in comps]; res['core_radius_provenance']=provenance
            res['rr_residual']=c.get('rr_residual'); res['rr_edge_cv']=c.get('rr_edge_cv'); res['walltime_total_s']=time.time()-t0
            art=res.pop('_artifacts')
            import numpy as np
            np.save(cdir/'operator_A.npy',art['operator_A'])
            from .io import write_csv
            write_csv(cdir/'spectrum.csv',art['mode_rows'])
            rr=res.get('radial_response',{}).get('rows',[])
            if rr: write_csv(cdir/'radial_response.csv',rr)
            write_json(cdir/'raw.json',_sanitize_for_json(res))
            rows.append({'case_id':cid,'status':'OK','runtime_s':res['walltime_total_s'],'backend':res['backend']})
        except Exception as e:
            err={'case_id':cid,'status':'ERROR','error_type':type(e).__name__,'error':str(e),'walltime_total_s':time.time()-t0}
            write_json(cdir/'raw.json',err); rows.append(err)
    write_json(results/'blind_run_summary.json',rows)
    return rows
