from __future__ import annotations

import math
import numpy as np


def polygon_curvature(points):
    p=np.asarray(points,float)
    pm=np.roll(p,1,axis=0); pp=np.roll(p,-1,axis=0)
    a=p-pm; b=pp-p; c=pp-pm
    na=np.linalg.norm(a,axis=1); nb=np.linalg.norm(b,axis=1); nc=np.linalg.norm(c,axis=1)
    cross=np.linalg.norm(np.cross(a,b),axis=1)
    den=na*nb*nc
    k=np.zeros(len(p),float)
    mask=den>1e-15
    k[mask]=2.0*cross[mask]/den[mask]
    return k


def centerline_geometry_audit(points,L,sigma,N,thresholds=None):
    thresholds=dict(thresholds or {})
    min_cells=float(thresholds.get('cells_per_sigma_min',4.0))
    max_slender=float(thresholds.get('three_sigma_kappa_max',0.5))
    min_clearance=float(thresholds.get('periodic_clearance_sigma_min',3.0))
    p=np.asarray(points,float)
    dx=float(L)/int(N)
    k=polygon_curvature(p)
    kmax=float(np.max(k)) if len(k) else float('nan')
    cells=float(sigma/dx)
    slender=float(3.0*sigma*kmax)
    centerline_clearance=float(0.5*L-np.max(np.abs(p)))
    clearance_sigma=float(centerline_clearance/sigma) if sigma>0 else -math.inf
    sigma_min_grid=min_cells*dx
    sigma_max_slender=(max_slender/(3.0*kmax)) if kmax>0 else math.inf
    joint_feasible_at_N=bool(sigma_min_grid<=sigma_max_slender and centerline_clearance>=min_clearance*sigma_min_grid)
    n_req_cells=math.ceil(min_cells*L/sigma) if sigma>0 else None
    n_req_joint=math.ceil(3.0*min_cells*L*kmax/max_slender) if kmax>0 and max_slender>0 else None
    gates={
        'grid_core_resolution': bool(cells>=min_cells),
        'thin_tube_curvature': bool(slender<=max_slender),
        'periodic_clearance': bool(clearance_sigma>=min_clearance),
    }
    return {
        'N':int(N),'L':float(L),'dx':dx,'core_sigma':float(sigma),
        'cells_per_sigma':cells,'cells_per_sigma_min':min_cells,
        'kappa_max_polyline':kmax,'three_sigma_kappa_max':slender,'three_sigma_kappa_limit':max_slender,
        'centerline_periodic_clearance':centerline_clearance,'periodic_clearance_sigma':clearance_sigma,
        'periodic_clearance_sigma_min':min_clearance,'sigma_min_for_grid_gate':sigma_min_grid,
        'sigma_max_for_slender_gate':sigma_max_slender,'joint_sigma_feasible_at_N':joint_feasible_at_N,
        'N_required_cells_at_current_sigma':n_req_cells,'N_required_joint_grid_slender_estimate':n_req_joint,
        'gates':gates,'geometry_core_gate_pass':bool(all(gates.values())),
    }


def spectral_tail_fraction(uh,outer_fraction=0.8):
    """Energy fraction in the outer part of the retained 2/3 spectral cube."""
    N=uh.shape[1]
    n=np.fft.fftfreq(N)*N
    nx,ny,nz=np.meshgrid(n,n,n,indexing='ij')
    cut=max(1,N//3)
    retained=(np.abs(nx)<=cut)&(np.abs(ny)<=cut)&(np.abs(nz)<=cut)
    outer=retained & ((np.abs(nx)>=outer_fraction*cut)|(np.abs(ny)>=outer_fraction*cut)|(np.abs(nz)>=outer_fraction*cut))
    e=np.sum(np.abs(uh)**2,axis=0)
    den=float(np.sum(e[retained]))
    return 0.0 if den<=0 else float(np.sum(e[outer])/den)


def seed_spectral_audit(uh,thresholds=None):
    thresholds=dict(thresholds or {})
    limit=float(thresholds.get('spectral_tail_fraction_max',0.08))
    frac=spectral_tail_fraction(uh,float(thresholds.get('spectral_outer_fraction',0.8)))
    return {'spectral_tail_fraction':frac,'spectral_tail_fraction_max':limit,'spectral_bandlimit_gate_pass':bool(frac<=limit)}


def _observed_order_grid(Ns,vals):
    Ns=np.asarray(Ns,float); vals=np.asarray(vals,float)
    if len(Ns)!=3 or not np.isfinite(vals).all(): return None
    d12=abs(vals[0]-vals[1]); d23=abs(vals[1]-vals[2])
    scale=max(abs(vals).max(),1e-30)
    if max(d12,d23)<=1e-12*scale: return {'state':'NUMERICAL_FLOOR','p_observed':None,'ratio_mismatch':0.0}
    if d12<=0 or d23<=0: return {'state':'UNRESOLVED','p_observed':None,'ratio_mismatch':None}
    obs=d12/d23
    ps=np.linspace(0.1,8.0,7901)
    pred=np.abs(Ns[0]**(-ps)-Ns[1]**(-ps))/np.maximum(np.abs(Ns[1]**(-ps)-Ns[2]**(-ps)),1e-300)
    i=int(np.argmin(np.abs(np.log(pred)-math.log(obs))))
    return {'state':'ORDER_ESTIMATE','p_observed':float(ps[i]),'ratio_mismatch':float(abs(math.log(pred[i]/obs)))}


def spatial_convergence(rows,gate=None):
    gate=dict(gate or {})
    rel_tol=float(gate.get('finest_relative_change_max',0.05))
    p_min=float(gate.get('observed_order_min',1.0))
    observables=list(gate.get('observables',['omega_growth','bkm_integral']))
    rows=sorted(rows,key=lambda r:int(r['N']))
    result={'Ns':[int(r['N']) for r in rows],'observables':{},'pass':True}
    if len(rows)<3 or len(set(result['Ns']))<3:
        return {**result,'pass':False,'reason':'need_three_distinct_spatial_resolutions'}
    use=rows[-3:]; Ns=[r['N'] for r in use]
    for key in observables:
        vals=[float(r[key]) for r in use]
        q=_observed_order_grid(Ns,vals)
        fine_change=abs(vals[-1]-vals[-2])/max(abs(vals[-1]),abs(vals[-2]),1e-30)
        floor=bool(q and q['state']=='NUMERICAL_FLOOR')
        passed=bool(fine_change<=rel_tol and (floor or (q and q.get('p_observed') is not None and q['p_observed']>=p_min)))
        result['observables'][key]={'values':vals,'finest_relative_change':fine_change,'finest_relative_change_max':rel_tol,**(q or {}),'pass':passed}
        result['pass']=result['pass'] and passed
    return result


def temporal_convergence(rows,gate=None):
    gate=dict(gate or {})
    p_min=float(gate.get('observed_order_min',2.8))
    rel_floor=float(gate.get('relative_numerical_floor',1e-7))
    observables=list(gate.get('observables',['omega_growth','bkm_integral']))
    rows=sorted(rows,key=lambda r:float(r['dt']),reverse=True)
    out={'dts':[float(r['dt']) for r in rows],'observables':{},'pass':True}
    if len(rows)<3:
        return {**out,'pass':False,'reason':'need_three_timestep_levels'}
    use=rows[:3]
    dts=np.array([r['dt'] for r in use],float)
    if not (abs(dts[0]/dts[1]-2)<1e-6 and abs(dts[1]/dts[2]-2)<1e-6):
        return {**out,'pass':False,'reason':'timestep_levels_must_be_dt_dt2_dt4'}
    for key in observables:
        vals=np.array([r[key] for r in use],float)
        d1=abs(vals[0]-vals[1]); d2=abs(vals[1]-vals[2]); scale=max(float(np.max(np.abs(vals))),1e-30)
        if max(d1,d2)/scale<=rel_floor:
            state='NUMERICAL_FLOOR'; p=None; passed=True
        elif d1>0 and d2>0:
            p=float(math.log(d1/d2,2.0)); state='ORDER_ESTIMATE'; passed=bool(p>=p_min)
        else:
            p=None; state='UNRESOLVED'; passed=False
        out['observables'][key]={'values':[float(x) for x in vals],'state':state,'p_observed':p,'observed_order_min':p_min,'pass':passed}
        out['pass']=out['pass'] and passed
    return out
