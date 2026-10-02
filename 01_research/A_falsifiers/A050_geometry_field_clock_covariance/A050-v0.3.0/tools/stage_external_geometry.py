from __future__ import annotations
import argparse,json,hashlib,os,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sst_gfcc_blind.geometry import resample_closed
from sst_gfcc_blind.modes import bishop_frame,kabsch_align
from pklsa_stage_lib import load_source

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def center_scale(p):
 p=np.asarray(p,float); p=p-p.mean(0,keepdims=True); r=np.sqrt(np.mean(np.sum(p*p,axis=1)))
 if not np.isfinite(r) or r<=0: raise ValueError('degenerate source curve')
 return p/r

def normalize(p,n): return resample_closed(center_scale(p),int(n))
def direction(base,seed):
 rng=np.random.default_rng(int(seed)); t,n,b=bishop_frame(base); s=np.arange(len(base),dtype=float)
 d=np.zeros_like(base)
 for m in range(2,9):
  a,b0,c,d0=rng.normal(size=4); ph=2*np.pi*m*s/len(base)
  d+=(a*np.cos(ph)+b0*np.sin(ph))[:,None]*n+(c*np.cos(ph)+d0*np.sin(ph))[:,None]*b
 d=d-np.sum(d*t,axis=1,keepdims=True)*t
 d-=d.mean(0,keepdims=True); rms=np.sqrt(np.mean(np.sum(d*d,axis=1)))
 return d/max(rms,1e-15)
def measured_rms(p,base):
 q=kabsch_align(p,base); return float(np.sqrt(np.mean(np.sum((q-base)**2,axis=1))))
def locate_root(arg):
 if arg:
  p=Path(arg).resolve()
  if p.exists(): return p
 env=os.environ.get('SST_WORKBENCH_ROOT')
 if env and Path(env).exists(): return Path(env).resolve()
 here=ROOT.resolve()
 for p in [here,*here.parents]:
  if (p/'03_data').exists() and (p/'10_docs').exists(): return p
 p=Path(r'C:\workspace\projects\SST-Workbench')
 if p.exists(): return p.resolve()
 raise RuntimeError('SST-Workbench root not found. Pass --workbench-root or set SST_WORKBENCH_ROOT.')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--workbench-root'); ap.add_argument('--config',default='config/default.json'); a=ap.parse_args()
 cfg=json.loads((ROOT/a.config).read_text(encoding='utf-8')); wb=locate_root(a.workbench_root)
 panel=json.loads((ROOT/'reveal/SOURCE_PANEL_v0.3.0.json').read_text(encoding='utf-8'))
 staged_rel=cfg['external_geometry_gate']['staged_manifest']; staged_path=ROOT/staged_rel
 stage_dir=staged_path.parent/('staged_extended_blind' if 'EXTENDED' in staged_path.name else 'staged_real_blind')
 stage_dir.mkdir(parents=True,exist_ok=True)
 # clear stale npz files to prevent accidental mixed-config reuse
 for p in stage_dir.glob('*.npz'): p.unlink()
 out=[]; reveal=[]; n=int(cfg['curve_points']); eps=float(cfg['external_geometry_gate']['perturbation_rms']); reps=int(cfg['external_geometry_gate']['holdout_replicates_per_primary_base'])
 for k,e in enumerate(panel['entries']):
  raw,src,rawhash=load_source(e,wb); base=normalize(raw,n); aid=e['anonymous_base_id']
  bfile=stage_dir/f'{aid}_BASE.npz'; np.savez_compressed(bfile,points=base)
  out.append({'carrier_id':f'{aid}_BASE','group_id':aid,'source_group_id':e['anonymous_source_group'],'role':'baseline','primary':e['panel_role']=='primary','file':str(bfile.relative_to(ROOT)).replace('\\','/'),'sha256':sha(bfile),'perturbation_rms':0.0})
  rev={'anonymous_base_id':aid,'carrier_id':e['carrier_id'],'source_family':e['source_family'],'provider_group':e['provider_group'],'catalog_id':e['catalog_id'],'source_role':e['source_role'],'method_group':e['method_group'],'relative_source_path':e['relative_source_path'],'raw_sha256_verified':rawhash,'staged_baseline_sha256':sha(bfile),'staged_points':n}
  reveal.append(rev)
  if e['panel_role']=='primary':
   for r in range(1,reps+1):
    seed=int(cfg['seed'])+10000*(k+1)+r; d=direction(base,seed); q=normalize(base+eps*d,n); mr=measured_rms(q,base)
    f=stage_dir/f'{aid}_H{r:02d}.npz'; np.savez_compressed(f,points=q)
    out.append({'carrier_id':f'{aid}_H{r:02d}','group_id':aid,'source_group_id':e['anonymous_source_group'],'role':'holdout','primary':True,'file':str(f.relative_to(ROOT)).replace('\\','/'),'sha256':sha(f),'perturbation_rms':mr})
  print(f'[stage] {aid} <- verified external geometry; n={n}',flush=True)
 manifest={'schema':'A050-V030-STAGED-BLIND-1','version':'v0.3.0','blind':True,'curve_points':n,'entries':out,'source_group_thresholds':cfg['external_geometry_gate']['source_group_minimum_robust_bases']}
 staged_path.write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8')
 rr=ROOT/'reveal'/('STAGE_RUNTIME_EXTENDED.json' if 'EXTENDED' in staged_path.name else 'STAGE_RUNTIME_DEFAULT.json')
 rr.write_text(json.dumps({'workbench_root':str(wb),'entries':reveal},indent=2,sort_keys=True),encoding='utf-8')
 print(f'[stage] {len(out)} anonymous staged curves -> {staged_path}')
if __name__=='__main__': main()
