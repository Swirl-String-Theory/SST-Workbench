from __future__ import annotations
import numpy as np
from .geometry import as_closed,resample_closed,normalize_by_reach,total_length,descriptors,linking_number
from .energy import energy_matrix,total_kernel
from .dynamics import potential_factory,gradient_only,gradient_hessian,split_flat,mode_ringdown


def allocate_resample(components,total_n):
    cs=[as_closed(c) for c in components]
    L=[np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in cs]; Lt=max(sum(L),1e-15)
    ns=[max(24,int(round(total_n*x/Lt))) for x in L]
    # preserve requested total approximately without ever dropping below 24
    return [resample_closed(c,n) for c,n in zip(cs,ns)]


def recondition(components,counts):
    cs=[resample_closed(c,n) for c,n in zip(components,counts)]
    norm,scale,detail=normalize_by_reach(cs)
    return norm,scale,detail


def clearance_proxy(components):
    cs=[as_closed(c) for c in components]; best=np.inf
    for ci,a in enumerate(cs):
        n=len(a); excl=max(3,n//20)
        # point-distance proxy excluding local arclength neighbors
        for i in range(n):
            d=np.linalg.norm(a[i]-a,axis=1); idx=np.arange(n); sep=np.minimum((idx-i)%n,(i-idx)%n); mask=sep>excl
            if np.any(mask): best=min(best,float(np.min(d[mask])))
        for b in cs[ci+1:]:
            for s in range(0,len(a),128):
                d=np.linalg.norm(a[s:s+128,None,:]-b[None,:,:],axis=2)
                if d.size: best=min(best,float(d.min()))
    return float(best) if np.isfinite(best) else None


def linking_vector(components):
    cs=[as_closed(c) for c in components]; vals=[]
    for i in range(len(cs)):
        for j in range(i+1,len(cs)): vals.append(float(linking_number(cs[i],cs[j])))
    return vals


def topology_proxy(initial_clearance, initial_links, components, clearance_retention=0.6, link_drift_max=0.05):
    c=clearance_proxy(components); links=linking_vector(components)
    floor=(initial_clearance*clearance_retention) if initial_clearance is not None else 0.0
    clearance_ok=(c is not None and c>=floor)
    if initial_links:
        link_drift=max(abs(a-b) for a,b in zip(initial_links,links)) if len(links)==len(initial_links) else float('inf')
        linking_ok=link_drift<=link_drift_max
    else:
        link_drift=0.0; linking_ok=True
    return {'clearance':c,'clearance_floor':floor,'clearance_ok':bool(clearance_ok),'linking':links,'linking_drift':float(link_drift),'linking_ok':bool(linking_ok),'ok':bool(clearance_ok and linking_ok)}


def cyclic_kabsch_rmsd(a,b):
    a=as_closed(a); b=as_closed(b)
    if len(a)!=len(b): b=resample_closed(b,len(a))
    A=a-a.mean(0); best=np.inf
    # orientation reversal is permitted as a parameterization equivalence, not a mirror transform.
    for B0 in (b, b[::-1]):
        B0=B0-B0.mean(0)
        for sh in range(len(A)):
            B=np.roll(B0,sh,axis=0); C=A.T@B; U,_,Vt=np.linalg.svd(C); R=Vt.T@U.T
            if np.linalg.det(R)<0:
                Vt[-1]*=-1;R=Vt.T@U.T
            d=A-B@R.T; rms=float(np.sqrt(np.mean(np.sum(d*d,axis=1)))); best=min(best,rms)
    return float(best)


def relax_variational(components,cfg):
    n=int(cfg['selector_resolution']); modes=int(cfg['selector_modes']); core=float(cfg.get('core_scale',1.0)); eps=float(cfg['fd_eps'])
    cs=allocate_resample(components,n); cs,source_reach,_=normalize_by_reach(cs); counts=[len(c) for c in cs]
    initial_clear=clearance_proxy(cs); initial_links=linking_vector(cs); initial_desc=descriptors(cs)
    initial_energy=total_kernel(energy_matrix(cs,core))
    history=[]; reason='max_iterations'
    for it in range(int(cfg['max_iterations'])):
        U,B,offs=potential_factory(cs,core,modes); u0,g=gradient_only(U,len(B),eps); sigma=float(np.linalg.norm(g)/max(abs(u0),1e-12))
        history.append({'iteration':it,'energy':u0,'stationarity':sigma,'gradient_norm':float(np.linalg.norm(g))})
        if sigma<=float(cfg['stationarity_max']): reason='stationarity_reached'; break
        ng=float(np.linalg.norm(g))
        if ng<=1e-15: reason='zero_gradient'; break
        direction=-g/ng; accepted=False; step=float(cfg['step0'])
        flat=np.vstack(cs)
        for bt in range(int(cfg['max_backtracks'])):
            trial_flat=flat+np.tensordot(step*direction,B,axes=(0,0)); trial=split_flat(trial_flat,offs)
            try: trial,_,_=recondition(trial,counts)
            except Exception: step*=0.5; continue
            e=total_kernel(energy_matrix(trial,core)); topo=topology_proxy(initial_clear,initial_links,trial,float(cfg['clearance_retention']),float(cfg['link_drift_max']))
            if np.isfinite(e) and e<=u0+1e-10*max(1.0,abs(u0)) and topo['ok']:
                cs=trial; accepted=True; history[-1].update({'accepted_step':step,'backtracks':bt,'trial_energy':e,'topology_proxy':topo}); break
            step*=0.5
        if not accepted:
            history[-1].update({'accepted_step':None,'backtracks':int(cfg['max_backtracks'])})
            reason='line_search_stalled'; break
    U,B,offs=potential_factory(cs,core,modes); uf,gf,K=gradient_hessian(U,len(B),eps); sigmaf=float(np.linalg.norm(gf)/max(abs(uf),1e-12))
    topo=topology_proxy(initial_clear,initial_links,cs,float(cfg['clearance_retention']),float(cfg['link_drift_max']))
    eig=np.linalg.eigvalsh(.5*(K+K.T)); maxabs=max(float(np.max(np.abs(eig))) if len(eig) else 0.0,1e-30)
    stable=bool(sigmaf<=float(cfg['stationarity_max']) and len(eig)>0 and float(eig.min())>=-float(cfg['hessian_negative_relative_tolerance'])*maxabs)
    ring=mode_ringdown(U,K,float(cfg['ringdown_perturb_eps']),float(cfg['ringdown_dt']),int(cfg['ringdown_steps'])) if stable else {'evaluated':False,'reason':'endpoint_not_stationary_stable_candidate'}
    ring_bounded=bool(ring.get('evaluated') and ring.get('amplitude_ratio',float('inf'))<=float(cfg['ringdown_amplitude_ratio_max']) and ring.get('hamiltonian_relative_drift',float('inf'))<=float(cfg['ringdown_energy_drift_max']))
    final_desc=descriptors(cs)
    return {
      'components':cs,
      'source_reach':source_reach,
      'initial_energy':float(initial_energy),'final_energy':float(uf),'energy_relative_change':float((uf-initial_energy)/max(abs(initial_energy),1e-30)),
      'initial_descriptors':initial_desc,'final_descriptors':final_desc,
      'initial_clearance':initial_clear,'initial_linking':initial_links,'topology_proxy':topo,
      'final_gradient_norm':float(np.linalg.norm(gf)),'final_stationarity':sigmaf,'stationarity_threshold':float(cfg['stationarity_max']),
      'stationary':bool(sigmaf<=float(cfg['stationarity_max'])),'hessian_eigenvalues':eig.tolist(),'hessian_symmetry_rel':float(np.linalg.norm(K-K.T)/max(np.linalg.norm(K),1e-30)),
      'stable_candidate':stable,'ringdown':ring,'ringdown_bounded':ring_bounded,
      'termination_reason':reason,'iterations_recorded':len(history),'history':history,
    }
