from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import time
import numpy as np

from .pklsa_adapter import PKLSARepository, PKLSACarrier
from .native import circulation_from_centerlines, mutual_helicity_from_components, backend_status


def _unit(x):
    x=np.asarray(x,float); return x/max(np.linalg.norm(x),np.finfo(float).tiny)


def resample_closed(c,n):
    c=np.asarray(c,float)
    if len(c)>1 and np.linalg.norm(c[0]-c[-1])<1e-14: c=c[:-1]
    q=np.vstack([c,c[0]]); ds=np.linalg.norm(np.diff(q,axis=0),axis=1); cum=np.r_[0,np.cumsum(ds)]
    L=cum[-1]
    if not np.isfinite(L) or L<=0: raise ValueError('degenerate closed component')
    t=np.arange(int(n),dtype=float)*L/int(n)
    idx=np.searchsorted(cum,t,side='right')-1; idx=np.clip(idx,0,len(c)-1)
    f=(t-cum[idx])/np.maximum(ds[idx],np.finfo(float).tiny)
    return np.ascontiguousarray(q[idx]*(1-f[:,None])+q[idx+1]*f[:,None],float)


def _frame(c,i):
    n=len(c); t=_unit(c[(i+1)%n]-c[(i-1)%n])
    axes=np.eye(3); ref=axes[int(np.argmin(np.abs(t)))]
    n1=_unit(np.cross(t,ref)); n2=_unit(np.cross(t,n1))
    return t,n1,n2


def _circle(center,n1,n2,r,n,turns=1,orientation=1):
    theta=orientation*np.arange(int(n),dtype=float)*(2*np.pi*int(turns)/int(n))
    return np.ascontiguousarray(center+r*(np.cos(theta)[:,None]*n1+np.sin(theta)[:,None]*n2),float)


def _construct_probe(repo:PKLSARepository, components, component_index:int, reach:float|None, nprobe:int, safety_factor:float, station_trials:int=12):
    c=components[component_index]
    # Reach is in E010 normalized coordinates. If unavailable, use a conservative local chord scale, then validate topology exactly.
    if reach and np.isfinite(reach) and reach>0:
        r0=float(reach)*float(safety_factor)
    else:
        chords=np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1)
        r0=max(float(np.median(chords))*2.0,1e-4)
    best=None
    for k in range(min(station_trials,len(c))):
        i=int((k+0.5)*len(c)/min(station_trials,len(c)))%len(c)
        t,n1,n2=_frame(c,i)
        for rf in (1.0,0.75,0.5,0.35):
            p=_circle(c[i],n1,n2,r0*rf,nprobe)
            lks=[]; back=None
            for s in components:
                lk,b=repo.exact_linking(s,p); lks.append(lk); back=b
            total=float(sum(lks))
            err=abs(abs(total)-1.0)
            cand=(err,p,total,lks,t,n1,n2,r0*rf,back)
            if best is None or err<best[0]: best=cand
            if err<2e-3: break
        if best and best[0]<2e-3: break
    if best is None or best[0]>=0.05:
        raise RuntimeError(f'could not construct a validated meridian probe; best | |Lk|-1 |={None if best is None else best[0]}')
    _,p,total,lks,t,n1,n2,r,back=best
    if total<0:
        p=p[::-1].copy(); total=-total; lks=[-x for x in lks]
    return p,{'target_linking':float(total),'component_linking':[float(x) for x in lks],'probe_radius':float(r),'exact_backend':back,'tangent':t.tolist(),'n1':n1.tolist(),'n2':n2.tolist()}


def _fit_lk(points):
    x=np.asarray([p['Lk_exact'] for p in points],float); y=np.asarray([p['circulation'] for p in points],float)
    A=np.c_[np.ones(len(x)),x]; coef=np.linalg.lstsq(A,y,rcond=None)[0]; pred=A@coef
    ssr=float(np.sum((y-pred)**2)); sst=float(np.sum((y-y.mean())**2)); r2=1-ssr/sst if sst>0 else 1.0
    return float(coef[0]),float(coef[1]),float(r2)


def run_m6_case(repo,carrier,components,cfg,threads=0,force_python=False):
    tc=cfg['topology_track']; ns=int(tc['source_resample_points']); npb=int(tc['probe_points'])
    comps=[resample_closed(c,ns) for c in components]
    case_points=[]; component_results=[]
    for ci in range(len(comps)):
        probe,meta=_construct_probe(repo,comps,ci,carrier.reach,npb,float(tc.get('meridian_radius_reach_factor',0.45)))
        # Positive, negative, double-winding, and topologically-null controls.
        controls=[]
        controls.append(('plus1',probe))
        controls.append(('minus1',probe[::-1].copy()))
        # Same meridian traversed twice. It is intentionally a winding-number control, not a simple embedded Hopf component.
        c=comps[ci]; idx=0; t,n1,n2=_frame(c,idx)
        # Use the validated probe's actual center/radius/frame as reconstructed from its centroid.
        ctr=np.mean(probe,axis=0); rr=float(np.mean(np.linalg.norm(probe-ctr,axis=1)))
        controls.append(('plus2_winding',_circle(ctr,np.asarray(meta['n1']),np.asarray(meta['n2']),rr,npb*2,turns=2)))
        extent=max(np.ptp(np.vstack(comps),axis=0).max(),1.0)
        null_probe=probe + np.asarray(meta['n1'])*5.0*extent
        controls.append(('null',null_probe))
        rows=[]
        for name,p in controls:
            lk_parts=[]; exact_backend=None
            for s in comps:
                lk,exact_backend=repo.exact_linking(s,p); lk_parts.append(lk)
            lk=float(sum(lk_parts))
            q,binfo=circulation_from_centerlines(comps,p,gamma=1.0,threads=threads,force_python=force_python)
            row={'control':name,'Lk_exact':lk,'Lk_parts':[float(z) for z in lk_parts],'circulation':float(q),'relative_to_topology':float(q/lk) if abs(lk)>1e-10 else None,'exact_backend':exact_backend,'biot_savart_backend':binfo.get('backend')}
            rows.append(row); case_points.append(row)
        component_results.append({'component_index':ci,'probe':{k:v for k,v in meta.items() if k not in ('tangent','n1','n2')},'controls':rows})
    a,b,r2=_fit_lk(case_points)
    nulls=[abs(x['circulation']) for x in case_points if abs(x['Lk_exact'])<0.1]
    nonzero=[x for x in case_points if abs(x['Lk_exact'])>0.5]
    slope_errors=[abs((x['circulation']/x['Lk_exact'])-1.0) for x in nonzero]
    return {
        'carrier':carrier.blind_summary(), 'component_count':len(comps), 'component_results':component_results,
        'fit':{'intercept':a,'slope':b,'r2':r2},
        'metrics':{'max_unit_slope_abs_error':float(max(slope_errors) if slope_errors else math.inf),'max_null_abs_circulation':float(max(nulls) if nulls else math.inf),'exact_linking_integer_max_residual':float(max(abs(x['Lk_exact']-round(x['Lk_exact'])) for x in case_points))},
    }


def run_m7_case(repo,carrier,components,cfg,threads=0,force_python=False):
    tc=cfg['topology_track']; ns=int(tc['source_resample_points'])
    comps=[resample_closed(c,ns) for c in components]
    if len(comps)<2: return None
    pair=[]; top=0.0; max_int=0.0; exact_backend=None
    for i in range(len(comps)):
        for j in range(i+1,len(comps)):
            lk,exact_backend=repo.exact_linking(comps[i],comps[j]); top += 2.0*lk; max_int=max(max_int,abs(lk-round(lk)))
            pair.append({'i':i,'j':j,'Lk_exact':float(lk)})
    h,binfo=mutual_helicity_from_components(comps,gammas=[1.0]*len(comps),threads=threads,force_python=force_python)
    denom=max(abs(top),1.0); rel=abs(h-top)/denom
    # Orientation reversal of one component: recompute both targets; this must not be confused with a global reversal.
    rev=[c.copy() for c in comps]; rev[0]=rev[0][::-1].copy()
    top_rev=0.0
    for i in range(len(rev)):
        for j in range(i+1,len(rev)):
            lk,_=repo.exact_linking(rev[i],rev[j]); top_rev += 2.0*lk
    h_rev,_=mutual_helicity_from_components(rev,gammas=[1.0]*len(rev),threads=threads,force_python=force_python)
    rel_rev=abs(h_rev-top_rev)/max(abs(top_rev),1.0)
    return {
        'carrier':carrier.blind_summary(),'component_count':len(comps),'pairs':pair,'exact_backend':exact_backend,'biot_savart_backend':binfo.get('backend'),
        'metrics':{'H_mutual_biot_savart':float(h),'H_mutual_topological':float(top),'relative_error':float(rel),'orientation_reversal_H':float(h_rev),'orientation_reversal_target':float(top_rev),'orientation_reversal_relative_error':float(rel_rev),'exact_linking_integer_max_residual':float(max_int)}
    }


def _status(gates):
    return 'FAIL' if any(g['status']=='FAIL' for g in gates) else ('INCONCLUSIVE' if any(g['status']=='INCONCLUSIVE' for g in gates) else 'PASS')


def run_topology(repo:PKLSARepository,outdir:Path,cfg:dict,threads=0,force_python=False):
    outdir.mkdir(parents=True,exist_ok=True); t0=time.perf_counter()
    if cfg.get('runtime',{}).get('require_pklsa_native',False) and repo.native is None:
        raise RuntimeError('Profile requires the E010 PKLSA native exact-linking backend. Install/build E010-v0.3.x in this venv (run_00_install.cmd does this).')
    sel=cfg['selection']; carriers,admission=repo.discover(cfg['pklsa_admission'],sel.get('topology_include') or None,int(sel.get('max_topologies',0)),int(sel.get('max_carriers_per_topology',0)))
    if not carriers: raise RuntimeError('PKLSA admission produced zero source-native carriers')
    m6=[]; m7=[]; load_fail=[]
    for k,c in enumerate(carriers,1):
        print(f"[3_MAXWELL][PKLSA] {k}/{len(carriers)} blind-carrier {c.blind_summary()['carrier_h']}",flush=True)
        try:
            comps,verify=repo.load_verified(c,fseries_n=int(cfg['topology_track'].get('fseries_n',4096)))
            x=run_m6_case(repo,c,comps,cfg,threads=threads,force_python=force_python); x['source_verification']=verify; m6.append(x)
            y=run_m7_case(repo,c,comps,cfg,threads=threads,force_python=force_python)
            if y is not None: y['source_verification']=verify; m7.append(y)
        except Exception as exc:
            load_fail.append({'carrier':c.blind_summary(),'error_type':type(exc).__name__,'error_digest':hashlib.sha256(str(exc).encode()).hexdigest()})
            if cfg['pklsa_admission'].get('fail_closed_on_runtime_carrier_error',True):
                continue
    g=[]; q=cfg['gates']['topology']
    def add(name,value,ok,crit): g.append({'name':name,'value':value,'criterion':crit,'status':'PASS' if ok else 'FAIL'})
    add('pklsa.runtime_carrier_errors',len(load_fail),len(load_fail)<=q.get('runtime_carrier_errors_max',0),f"<= {q.get('runtime_carrier_errors_max',0)}")
    if m6:
        vals=[x['metrics']['max_unit_slope_abs_error'] for x in m6]; null=[x['metrics']['max_null_abs_circulation'] for x in m6]; lint=[x['metrics']['exact_linking_integer_max_residual'] for x in m6]; r2=[x['fit']['r2'] for x in m6]
        add('M6.unit_circulation_slope',float(max(vals)),max(vals)<=q['m6_unit_slope_abs_error_max'],f"<= {q['m6_unit_slope_abs_error_max']}")
        add('M6.null_circulation',float(max(null)),max(null)<=q['m6_null_abs_circulation_max'],f"<= {q['m6_null_abs_circulation_max']}")
        add('M6.exact_linking_integer',float(max(lint)),max(lint)<=q['exact_linking_integer_residual_max'],f"<= {q['exact_linking_integer_residual_max']}")
        add('M6.linear_fit_r2',float(min(r2)),min(r2)>=q['m6_fit_r2_min'],f">= {q['m6_fit_r2_min']}")
    else:
        g.append({'name':'M6.available','value':0,'criterion':'>= 1','status':'INCONCLUSIVE'})
    if m7:
        errs=[x['metrics']['relative_error'] for x in m7]; rev=[x['metrics']['orientation_reversal_relative_error'] for x in m7]; lint=[x['metrics']['exact_linking_integer_max_residual'] for x in m7]
        add('M7.mutual_helicity_linking',float(max(errs)),max(errs)<=q['m7_relative_error_max'],f"<= {q['m7_relative_error_max']}")
        add('M7.orientation_reversal',float(max(rev)),max(rev)<=q['m7_relative_error_max'],f"<= {q['m7_relative_error_max']}")
        add('M7.exact_linking_integer',float(max(lint)),max(lint)<=q['exact_linking_integer_residual_max'],f"<= {q['exact_linking_integer_residual_max']}")
    elif q.get('require_multicomponent_case',False):
        g.append({'name':'M7.multicomponent_available','value':0,'criterion':'>= 1','status':'INCONCLUSIVE'})
    stat=_status(g)
    slopes=[x['fit']['slope'] for x in m6]
    summary_metrics={
        'median_m6_dimensionless_slope':float(np.median(slopes)) if slopes else None,
        'm6_slope_cv':float(np.std(slopes,ddof=1)/max(abs(np.mean(slopes)),1e-300)) if len(slopes)>1 else 0.0 if slopes else None,
        'm6_max_unit_slope_abs_error':float(max([x['metrics']['max_unit_slope_abs_error'] for x in m6])) if m6 else None,
        'm6_max_null_abs_circulation':float(max([x['metrics']['max_null_abs_circulation'] for x in m6])) if m6 else None,
        'm7_max_relative_error':float(max([x['metrics']['relative_error'] for x in m7])) if m7 else None,
    }
    result={'status':stat,'upstream':admission,'runtime':{'backend':backend_status(force_build=False,verbose=False),'threads':threads,'elapsed_s':time.perf_counter()-t0,'carriers_attempted':len(carriers),'m6_cases':len(m6),'m7_cases':len(m7),'runtime_errors':len(load_fail)},'metrics':summary_metrics,'gates':g,'runtime_errors':load_fail,'interpretation':'M6 tests the circulation-linking identity using PKLSA exact polygonal linking as the topological target and an independent Maxwell-3 Biot-Savart line-integral kernel. M7 tests mutual helicity against pairwise linking. No SST circulation constant is available to blind pass/fail code.'}
    (outdir/'topology_verdict.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Large case ledgers remain separate so blind_report.json stays compact.
    (outdir/'M6_topological_circulation_cases.json').write_text(json.dumps(m6,indent=2),encoding='utf-8')
    (outdir/'M7_mutual_helicity_cases.json').write_text(json.dumps(m7,indent=2),encoding='utf-8')
    return result
