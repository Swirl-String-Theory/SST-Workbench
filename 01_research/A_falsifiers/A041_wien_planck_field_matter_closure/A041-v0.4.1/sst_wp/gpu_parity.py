from __future__ import annotations
import argparse, json, secrets
from pathlib import Path
import numpy as np
from .common import load_json, dump_json
from .pklsa_adapter import atlas_rows, normalized_candidate, opaque_token, write_gpu_batch
from .gpu_funnel import cpu_screen_batch, sycl_screen_batch
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean


def rel(a,b): return abs(float(a)-float(b))/max(abs(float(b)),1e-12)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('atlas_root');ap.add_argument('--config',required=True);ap.add_argument('--gpu-exe',default='gpu/sycl_funnel_fp32.exe');ap.add_argument('--out',required=True);ap.add_argument('--work',required=True);a=ap.parse_args()
    root=Path(__file__).resolve().parents[1];assert_blind_code_clean(root);cfg=load_json(a.config);assert_blind_config_clean(cfg)
    rows=atlas_rows(a.atlas_root); idx=[0,47,48*14+23,48*30+11,48*48+47]; rows=[rows[i] for i in idx]
    secret=secrets.token_hex(16);N=int(cfg.get('funnel_parity_resolution',64)); rec=[]
    for r in rows:
        rr,X,offs=normalized_candidate(a.atlas_root,r,N); oid=opaque_token(secret,rr['candidate_id'],'GP')
        nxt=np.full(N,-1,dtype=np.int32)
        for ci in range(len(offs)-1):
            aa,bb=int(offs[ci]),int(offs[ci+1]);nxt[aa:bb-1]=np.arange(aa+1,bb,dtype=np.int32);nxt[bb-1]=aa
        rec.append({'opaque_id':oid,'points':X,'offsets':offs,'next':nxt})
    core=float(cfg['core_fraction']);cfl=float(cfg.get('funnel_gpu_cfl',0.12));work=Path(a.work);work.mkdir(parents=True,exist_ok=True)
    batch=write_gpu_batch(work/'parity.bin',rec,N,core,cfl)
    gpu,meta=sycl_screen_batch(a.gpu_exe,batch,work/'parity_gpu.csv',work/'parity_meta.txt',0)
    cpu,_=cpu_screen_batch(rec,core,cfl,0,require_native=True); gm={q['opaque_id']:q for q in gpu};cm={q['opaque_id']:q for q in cpu}
    fields=['mean_speed','speed_cv','pair_strain_rms']; rowsout=[];mx=0
    for oid in gm:
        q={'opaque_id':oid}
        for k in fields:
            e=rel(gm[oid][k],cm[oid][k]);q[k+'_relerr']=e;mx=max(mx,e)
        rowsout.append(q)
    tol=float(cfg.get('funnel_gpu_parity_rel_tol',0.01)); result={'format':'SST-WP-GPU-PARITY-4.0','device_meta':meta,'candidate_count':len(rowsout),'max_relative_error':mx,'tolerance':tol,'pass':bool(mx<=tol),'records':rowsout,'identity_revealed':False}
    dump_json(a.out,result);print(json.dumps(result,indent=2));raise SystemExit(0 if result['pass'] else 2)
if __name__=='__main__':main()
