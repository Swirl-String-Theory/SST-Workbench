from __future__ import annotations
import argparse,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
from sst_gfcc_blind.geometry import resample_closed
from sst_gfcc_blind.modes import bishop_frame,kabsch_align

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def direction(base,seed):
    rng=np.random.default_rng(int(seed)); t,n,b=bishop_frame(base); s=np.arange(len(base),dtype=float); d=np.zeros_like(base)
    for m in range(2,9):
        a,b0,c,d0=rng.normal(size=4); ph=2*np.pi*m*s/len(base)
        d+=(a*np.cos(ph)+b0*np.sin(ph))[:,None]*n+(c*np.cos(ph)+d0*np.sin(ph))[:,None]*b
    d=d-np.sum(d*t,axis=1,keepdims=True)*t; d-=d.mean(0,keepdims=True); rms=np.sqrt(np.mean(np.sum(d*d,axis=1)))
    return d/max(rms,1e-15)

def normalize(p,n):
    p=np.asarray(p,float); p=p-p.mean(0,keepdims=True); r=np.sqrt(np.mean(np.sum(p*p,axis=1))); return resample_closed(p/max(r,1e-15),int(n))

def measured_rms(p,base):
    q=kabsch_align(p,base); return float(np.sqrt(np.mean(np.sum((q-base)**2,axis=1))))

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/default.json'); a=ap.parse_args(); cfg=json.loads((ROOT/a.config).read_text(encoding='utf-8')); gate=cfg['mechanism_gate']
    parent_path=ROOT/cfg['external_geometry_gate']['staged_manifest']; parent=json.loads(parent_path.read_text(encoding='utf-8'))
    out_path=ROOT/gate['fresh_staged_manifest']; stage_dir=out_path.parent/gate['fresh_stage_directory']; stage_dir.mkdir(parents=True,exist_ok=True)
    for p in stage_dir.glob('*.npz'): p.unlink()
    n=int(cfg['curve_points']); eps=float(gate['fresh_holdout_perturbation_rms']); reps=int(gate['fresh_holdout_replicates_per_primary_base']); seed0=int(gate['fresh_holdout_seed']); entries=[]
    baselines=[x for x in parent['entries'] if x['role']=='baseline']
    for k,e in enumerate(baselines):
        base_path=ROOT/e['file']; base=np.asarray(np.load(base_path,allow_pickle=False)['points'],float)
        if sha(base_path)!=e['sha256']: raise RuntimeError('parent staged baseline hash mismatch: '+e['carrier_id'])
        entries.append(dict(e))
        if not e.get('primary',False): continue
        for r in range(1,reps+1):
            seed=seed0+10000*(k+1)+r; d=direction(base,seed); q=normalize(base+eps*d,n); mr=measured_rms(q,base)
            f=stage_dir/f'{e["group_id"]}_V40H{r:02d}.npz'; np.savez_compressed(f,points=q)
            entries.append({'carrier_id':f'{e["group_id"]}_V40H{r:02d}','group_id':e['group_id'],'source_group_id':e['source_group_id'],'role':'holdout','primary':True,'file':str(f.relative_to(ROOT)).replace('\\','/'),'sha256':sha(f),'perturbation_rms':mr,'fresh_v040_holdout':True,'generation_seed':seed})
    manifest={'schema':'A050-V040-FRESH-STAGED-BLIND-1','version':'v0.4.0','blind':True,'curve_points':n,'parent_manifest':str(parent_path.relative_to(ROOT)).replace('\\','/'),'parent_manifest_sha256':sha(parent_path),'fresh_holdout_seed':seed0,'fresh_holdout_perturbation_rms_target':eps,'entries':entries,'source_group_thresholds':cfg['external_geometry_gate']['source_group_minimum_robust_bases']}
    out_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(f'[v0.4.0-stage] {len(entries)} carriers -> {out_path}')
if __name__=='__main__': main()
