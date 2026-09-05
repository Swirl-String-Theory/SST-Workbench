from __future__ import annotations
import argparse, json, math, secrets
from pathlib import Path
import numpy as np
from .common import load_json, dump_json, sha256_file, geometry_sha256
from .geometry import discover, load_geometry, normalize_components, spacing_metrics
from .kernels import velocity
from .dynamics import evolve
from .blind_guard import assert_blind_code_clean, assert_blind_config_clean


def _tangents(x):
    t=np.roll(x,-1,axis=0)-np.roll(x,1,axis=0)
    return t/np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-15)


def _rigid_normal_fit(x,u):
    x=np.asarray(x,float);u=np.asarray(u,float);c=x.mean(0);r=x-c;t=_tangents(x);I=np.eye(3);rows=[];rhs=[]
    for ri,ti,ui in zip(r,t,u):
        P=I-np.outer(ti,ti)
        S=np.array([[0,-ri[2],ri[1]],[ri[2],0,-ri[0]],[-ri[1],ri[0],0]],float)
        rows.append(P@np.hstack([I,-S]));rhs.append(P@ui)
    A=np.vstack(rows);y=np.hstack(rhs);q,*_=np.linalg.lstsq(A,y,rcond=None);V=q[:3];om=q[3:]
    fit=V[None,:]+np.cross(np.broadcast_to(om,r.shape),r)
    un=u-np.sum(u*t,axis=1)[:,None]*t;fn=fit-np.sum(fit*t,axis=1)[:,None]*t
    rr=float(np.sqrt(np.mean(np.sum((un-fn)**2,axis=1))));uu=float(np.sqrt(np.mean(np.sum(un*un,axis=1))))
    return {'coherence':float(max(0.0,1.0-rr/max(uu,1e-15))),'omega_mag':float(np.linalg.norm(om)),'translation_mag':float(np.linalg.norm(V)),'normal_rms':uu,'residual_rms':rr}


def _kabsch_rms(P,Q):
    P=np.asarray(P,float);Q=np.asarray(Q,float);Pc=P-P.mean(0);Qc=Q-Q.mean(0);H=Pc.T@Qc;U,S,Vt=np.linalg.svd(H);R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1;R=Vt.T@U.T
    A=Pc@R
    return float(np.sqrt(np.mean(np.sum((A-Qc)**2,axis=1))))


def qualify(path,cfg):
    comps=load_geometry(path);N=int(cfg.get('qualification_resolution',64));X,offs=normalize_components(comps,N)
    gamma=float(cfg.get('gamma_dimensionless',1.0));core=float(cfg['core_fraction']);req=bool(cfg.get('require_native',False))
    u=velocity(X,offs,gamma,core,req);rf=_rigid_normal_fit(X,u)
    qcfg=dict(cfg);qcfg['t_final']=float(cfg.get('qualification_t_final',0.03));qcfg['samples']=int(cfg.get('qualification_samples',64));qcfg['reparameterization_events']=int(cfg.get('qualification_reparameterization_events',2))
    times,snaps,diag=evolve(X,offs,qcfg,qcfg['samples'],1.0)
    drift=_kabsch_rms(snaps[-1],X) if len(snaps) else float('inf')
    mesh=float(diag['mesh_cv_max_observed'])
    shape_scale=float(cfg.get('qualification_shape_scale',0.08));mesh_scale=float(cfg.get('qualification_mesh_scale',0.20))
    shape_term=math.exp(-drift/max(shape_scale,1e-12));mesh_term=math.exp(-mesh/max(mesh_scale,1e-12))
    w=cfg.get('qualification_score_weights',{'rolling':0.5,'shape':0.35,'mesh':0.15})
    score=float(w.get('rolling',0)*rf['coherence']+w.get('shape',0)*shape_term+w.get('mesh',0)*mesh_term)
    passed=bool(rf['coherence']>=float(cfg.get('qualification_min_rolling_coherence',0.05)) and drift<=float(cfg.get('qualification_max_shape_drift',0.25)) and mesh<=float(cfg.get('qualification_max_mesh_cv',0.25)))
    return {'score':score,'passed':passed,'rolling_coherence':rf['coherence'],'shape_drift':drift,'mesh_cv':mesh,'omega_mag_hat':rf['omega_mag'],'translation_mag_hat':rf['translation_mag'],'source_sha256':sha256_file(path),'geometry_sha256':geometry_sha256(X,offs),'resolution_N':N,'qualification_t_final_hat':qcfg['t_final'],'adaptive_reparameterizations':diag.get('adaptive_reparameterizations',0),'mesh_sample_cv':diag.get('sample_mesh_max_cv',mesh)}


def main():
    p=argparse.ArgumentParser();p.add_argument('dataset');p.add_argument('--config',required=True);p.add_argument('--out',required=True);p.add_argument('--selection',required=True);p.add_argument('--private-dir',default='private_reveal_keys');a=p.parse_args()
    root=Path(__file__).resolve().parents[1];assert_blind_code_clean(root);cfg=load_json(a.config);assert_blind_config_clean(cfg)
    files=discover(a.dataset);rows=[]
    for f in files:
        try: rows.append({'path':str(f),**qualify(f,cfg)})
        except Exception as e: rows.append({'path':str(f),'passed':False,'score':-1.0,'error':repr(e)})
    eligible=[r for r in rows if r.get('passed')]
    eligible.sort(key=lambda r:(-float(r.get('score',-1)),str(r.get('geometry_sha256',''))))
    n=int(cfg.get('max_carriers',6));selected=eligible[:n]
    if not selected:
        raise SystemExit('No atlas candidates passed dimensionless seed qualification')
    # Public output contains only random opaque qualification ids and metrics, never source paths.
    opaque={r['path']:f'KQ_{secrets.token_hex(6)}' for r in rows}
    pub=[]
    for r in rows:
        pub.append({'qualification_id':opaque[r['path']],**{k:v for k,v in r.items() if k not in {'path','source_sha256','geometry_sha256'}}})
    # Do not preserve source-file ordering in the public qualification artifact.
    # Otherwise an observer who knows discover() sorting could recover identities by row position.
    secrets.SystemRandom().shuffle(pub)
    dump_json(a.out,{'format':'SST-WP-SEED-QUALIFICATION-PUBLIC-3.1','candidate_count':len(rows),'eligible_count':len(eligible),'selected_count':len(selected),'selection_policy':'score_descending_after_preregistered_dimensionless_qualification','public_row_order_randomized':True,'SST_canonical_constants_used':False,'SI_units_used':False,'records':pub})
    # Selection is identity-bearing and therefore quarantined outside blind outputs.
    priv=Path(a.private_dir);priv.mkdir(parents=True,exist_ok=True)
    selection={'format':'SST-WP-SEED-SELECTION-PRIVATE-3.1','dataset':str(Path(a.dataset).resolve()),'selected':[{'path':r['path'],'source_sha256':r.get('source_sha256'),'geometry_sha256':r.get('geometry_sha256'),'qualification_score':r.get('score'),'qualification_rank':i+1} for i,r in enumerate(selected)]}
    dump_json(a.selection,selection)
    print(json.dumps({'candidates':len(rows),'eligible':len(eligible),'selected':len(selected),'public_out':a.out,'private_selection':a.selection},indent=2))

if __name__=='__main__': main()
