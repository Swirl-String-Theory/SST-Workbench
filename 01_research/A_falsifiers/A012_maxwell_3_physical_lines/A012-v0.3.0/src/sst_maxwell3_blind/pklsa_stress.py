from __future__ import annotations
import json,math,time,hashlib
from pathlib import Path
import numpy as np
from .native import biot_savart_velocity,backend_status
from .topology_track import resample_closed


def _unit(v):
    n=np.linalg.norm(v,axis=-1,keepdims=True); return v/np.maximum(n,np.finfo(float).tiny)

def _frames(c):
    t=_unit(np.roll(c,-1,axis=0)-np.roll(c,1,axis=0)); n1=np.empty_like(t); n2=np.empty_like(t); axes=np.eye(3)
    for i,ti in enumerate(t):
        ref=axes[int(np.argmin(np.abs(ti)))]; q=np.cross(ti,ref); q=q/max(np.linalg.norm(q),np.finfo(float).tiny); n1[i]=q; n2[i]=np.cross(ti,q)
    return t,n1,n2

def _segments(comps):
    a=np.vstack(comps); b=np.vstack([np.roll(c,-1,axis=0) for c in comps]); return np.ascontiguousarray(a,float),np.ascontiguousarray(b,float)

def _case(repo,carrier,comps,cfg,threads,force_python):
    s=cfg['stress_track']; phys=cfg['physical_constants']; n=int(s['resample_points']); comps=[resample_closed(c,n) for c in comps]
    reach=float(carrier.reach or 0.0)
    if not np.isfinite(reach) or reach<=0: raise ValueError('PKLSA reach unavailable')
    pts=[]; tang=[]; ids=[]; refs=[]; ref_phi=[]; ref_ids=[]; sid=0
    for c in comps:
        t,n1,n2=_frames(c); ns=min(int(s['stations_per_component']),len(c)); idx=np.floor(np.arange(ns)*len(c)/ns).astype(int)
        angles=2*np.pi*(np.arange(int(s['angular_samples']))+.5)/int(s['angular_samples'])
        radii=reach*float(s['sample_radius_reach_factor'])*np.sqrt((np.arange(int(s['radial_samples']))+.5)/int(s['radial_samples']))
        for ii in idx:
            for r in radii:
                for a in angles:
                    er=math.cos(a)*n1[ii]+math.sin(a)*n2[ii]; pts.append(c[ii]+r*er); tang.append(t[ii]); ids.append(sid)
            rr=reach*float(s.get('vref_radius_reach_factor',1.0))
            for a in angles:
                er=math.cos(a)*n1[ii]+math.sin(a)*n2[ii]; refs.append(c[ii]+rr*er); ref_phi.append(np.cross(t[ii],er)); ref_ids.append(sid)
            sid+=1
    pts=np.asarray(pts,float); tang=np.asarray(tang,float); ids=np.asarray(ids,int); refs=np.asarray(refs,float); ref_phi=np.asarray(ref_phi,float); ref_ids=np.asarray(ref_ids,int)
    aa,bb=_segments(comps); allp=np.vstack([pts,refs]); u,info=biot_savart_velocity(allp,aa,bb,1.0,reach,threads=threads,force_python=force_python)
    ui=u[:len(pts)]; ur=u[len(pts):]
    vref=[]
    for i in range(sid):
        m=ref_ids==i; vref.append(abs(float(np.mean(np.sum(ur[m]*ref_phi[m],axis=1)))))
    vunit=float(np.median(vref)); vs=float(phys['v_swirl_m_s']); rho=float(phys['rho_f_kg_m3']); scale=vs/vunit; ui*=scale
    deltas=[]; aligns=[]; residuals=[]
    for i in range(sid):
        m=ids==i; us=ui[m]; tt=np.mean(tang[m],axis=0); tt=tt/max(np.linalg.norm(tt),1e-300); up=us-us.mean(axis=0); R=rho*(up.T@up)/len(up)
        ppar=float(tt@R@tt); pperp=.5*(float(np.trace(R))-ppar); delta=pperp-ppar
        model=pperp*np.eye(3)+(ppar-pperp)*np.outer(tt,tt); residuals.append(float(np.linalg.norm(R-model)/max(np.linalg.norm(R),1e-300)))
        vals,vec=np.linalg.eigh(R); aligns.append(abs(float(vec[:,0]@tt))); deltas.append(delta)
    C=float(np.median(deltas)/(rho*vs*vs))
    return {'carrier':carrier.blind_summary(),'component_count':len(comps),'reach':reach,'median_C_blind':C,'median_delta_pa':float(np.median(deltas)),'median_axisymmetry_residual':float(np.median(residuals)),'median_director_alignment':float(np.median(aligns)),'positive_anisotropy_fraction':float(np.mean(np.asarray(deltas)>0)),'backend':info.get('backend')}

def run_pklsa_stress(repo,carriers,outdir:Path,cfg,threads=0,force_python=False):
    s=cfg.get('stress_track',{});
    if not s.get('enabled',True): return {'status':'INCONCLUSIVE','reason':'disabled'}
    # Deterministic source-native anchors, at most one per topology unless certification asks otherwise.
    selected=[]; seen=set()
    for c in carriers:
        if c.reach is None or not np.isfinite(c.reach) or c.reach<=0: continue
        allowed=set(s.get('allowed_reach_status',['RESOLVED']))
        if c.observable_status.get('reach') not in allowed: continue
        if s.get('one_per_topology',True) and c.topology_id in seen: continue
        selected.append(c); seen.add(c.topology_id)
        if int(s.get('max_cases',0))>0 and len(selected)>=int(s['max_cases']): break
    cases=[]; errors=[]; t0=time.perf_counter()
    for c in selected:
        try:
            comps,_=repo.load_verified(c,fseries_n=int(cfg['topology_track'].get('fseries_n',4096))); cases.append(_case(repo,c,comps,cfg,threads,force_python))
        except Exception as e: errors.append({'carrier':c.blind_summary(),'error_type':type(e).__name__,'error_digest':hashlib.sha256(str(e).encode()).hexdigest()})
    q=cfg['gates']['stress']; gates=[]
    def add(n,v,ok,crit): gates.append({'name':n,'value':v,'criterion':crit,'status':'PASS' if ok else 'FAIL'})
    enough=len(cases)>=q['min_cases']
    gates.append({'name':'M1.accepted_stress_cases','value':len(cases),'criterion':f">= {q['min_cases']}",'status':'PASS' if enough else 'INCONCLUSIVE'})
    if enough:
        med_align=float(np.median([x['median_director_alignment'] for x in cases])); pos=float(np.mean([x['positive_anisotropy_fraction'] for x in cases])); med_res=float(np.median([x['median_axisymmetry_residual'] for x in cases]))
        add('M1.director_alignment',med_align,med_align>=q['median_director_alignment_min'],f">= {q['median_director_alignment_min']}")
        add('M1.positive_anisotropy',pos,pos>=q['positive_anisotropy_fraction_min'],f">= {q['positive_anisotropy_fraction_min']}")
        gates.append({'name':'M1.axisymmetry','value':med_res,'criterion':f"diagnostic <= {q['median_axisymmetry_residual_max']}",'status':'DIAGNOSTIC','meets_target':med_res<=q['median_axisymmetry_residual_max']})
    status='FAIL' if any(x['status']=='FAIL' for x in gates) else ('INCONCLUSIVE' if any(x['status']=='INCONCLUSIVE' for x in gates) else 'PASS')
    out={'status':status,'cases':cases,'errors':errors,'metrics':{'median_C_blind':float(np.median([x['median_C_blind'] for x in cases])) if cases else None},'gates':gates,'runtime':{'elapsed_s':time.perf_counter()-t0,'backend':backend_status(False,False)}}
    (outdir/'M1_M3_pklsa_stress_verdict.json').write_text(json.dumps(out,indent=2),encoding='utf-8'); return out
