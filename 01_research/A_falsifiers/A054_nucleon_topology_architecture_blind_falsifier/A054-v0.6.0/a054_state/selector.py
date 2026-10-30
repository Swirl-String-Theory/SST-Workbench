from __future__ import annotations
import numpy as np
from .geometry import as_closed,resample_closed,normalize_by_reach,descriptors,linking_number
from .energy import energy_matrix,total_kernel
from .dynamics import constrained_potential_factory,gradient_only,gradient_hessian_sweep,mode_ringdown


def allocate_resample(components,total_n):
    cs=[as_closed(c) for c in components]
    L=[np.linalg.norm(np.roll(c,-1,axis=0)-c,axis=1).sum() for c in cs]; Lt=max(sum(L),1e-15)
    ns=[max(24,int(round(total_n*x/Lt))) for x in L]
    return [resample_closed(c,n) for c,n in zip(cs,ns)]


def recondition(components,counts):
    cs=[resample_closed(c,n) for c,n in zip(components,counts)]
    norm,scale,detail=normalize_by_reach(cs)
    return norm,scale,detail


def clearance_proxy(components):
    cs=[as_closed(c) for c in components]; best=np.inf
    for ci,a in enumerate(cs):
        n=len(a); excl=max(3,n//20)
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
    for B0 in (b, b[::-1]):
        B0=B0-B0.mean(0)
        for sh in range(len(A)):
            B=np.roll(B0,sh,axis=0); C=A.T@B; U,_,Vt=np.linalg.svd(C); R=Vt.T@U.T
            if np.linalg.det(R)<0:
                Vt[-1]*=-1;R=Vt.T@U.T
            d=A-B@R.T; rms=float(np.sqrt(np.mean(np.sum(d*d,axis=1)))); best=min(best,rms)
    return float(best)


def _line_search(U,project,g,u0,initial_clear,initial_links,cfg,trust_radius):
    """Armijo backtracking on exactly the same constrained objective as the gradient.

    Returns an accepted projected geometry or a diagnostic explaining why descent
    could not be established.  A failure to demonstrate numerical descent is not
    silently converted into scientific evidence against state selection.
    """
    ng=float(np.linalg.norm(g))
    if not np.isfinite(ng) or ng<=1e-15:
        return {'accepted':False,'numerically_resolved':False,'reason':'numerical_gradient_degenerate','attempts':[],'trust_radius':float(trust_radius)}
    direction=-np.asarray(g,float)/ng
    slope=float(np.dot(g,direction)) # = -||g|| for a well-formed gradient
    beta=float(cfg.get('backtrack_factor',0.5)); c1=float(cfg.get('armijo_c1',1e-4))
    min_step=float(cfg.get('min_step',1e-7)); max_bt=int(cfg['max_backtracks'])
    atol=float(cfg.get('objective_abs_tolerance',1e-10)); rtol=float(cfg.get('objective_rel_tolerance',1e-10))
    tol=atol+rtol*max(1.0,abs(float(u0)))
    step=min(float(cfg['step0']),float(trust_radius)); attempts=[]
    finite_seen=False; descent_seen=False; feasible_descent_seen=False
    for bt in range(max_bt):
        if step<min_step: break
        rec={'backtrack':bt,'step':float(step)}
        try:
            trial,_,_=project(step*direction)
            e=float(U(step*direction)); finite=bool(np.isfinite(e)); finite_seen|=finite
            topo=topology_proxy(initial_clear,initial_links,trial,float(cfg['clearance_retention']),float(cfg['link_drift_max']))
            strict_descent=bool(finite and e < float(u0)-tol); descent_seen|=strict_descent
            feasible_descent=bool(strict_descent and topo['ok']); feasible_descent_seen|=feasible_descent
            armijo_rhs=float(u0)+c1*float(step)*slope
            armijo=bool(finite and e<=armijo_rhs+tol)
            rec.update({'trial_energy':e,'energy_delta':e-float(u0),'strict_descent':strict_descent,'armijo_rhs':armijo_rhs,'armijo':armijo,'topology_ok':bool(topo['ok'])})
            attempts.append(rec)
            if armijo and topo['ok']:
                return {'accepted':True,'numerically_resolved':True,'reason':'armijo_accepted','trial':trial,'energy':e,'step':float(step),'backtracks':bt,'topology_proxy':topo,'attempts':attempts,'trust_radius':float(trust_radius)}
        except Exception as ex:
            rec.update({'exception':f'{type(ex).__name__}: {ex}'});attempts.append(rec)
        step*=beta
    if not finite_seen:
        reason='numerical_objective_evaluation_unresolved'; resolved=False
    elif not descent_seen:
        reason='numerical_descent_not_demonstrated'; resolved=False
    elif not feasible_descent_seen:
        reason='topology_constraint_blocked'; resolved=True
    else:
        reason='numerical_armijo_not_resolved'; resolved=False
    return {'accepted':False,'numerically_resolved':bool(resolved),'reason':reason,'attempts':attempts,'trust_radius':float(trust_radius)}


def relax_variational(components,cfg):
    n=int(cfg['selector_resolution']); modes=int(cfg['selector_modes']); core=float(cfg.get('core_scale',1.0)); eps=float(cfg['fd_eps'])
    cs=allocate_resample(components,n); cs,source_reach,_=normalize_by_reach(cs); counts=[len(c) for c in cs]
    initial_clear=clearance_proxy(cs); initial_links=linking_vector(cs); initial_desc=descriptors(cs)
    source_energy_before_objective=float(total_kernel(energy_matrix(cs,core)))
    history=[]; reason='max_iterations'; optimizer_resolved=True; trust_radius=float(cfg.get('trust_radius_initial',cfg['step0']))
    initial_energy=None
    for it in range(int(cfg['max_iterations'])):
        U,project,B,offs,base=constrained_potential_factory(cs,core,modes,counts);cs=base
        u0,g=gradient_only(U,len(B),eps)
        if initial_energy is None: initial_energy=float(u0)
        sigma=float(np.linalg.norm(g)/max(abs(u0),1e-12))
        hist={'iteration':it,'objective':'U_c_reconditioned','energy':float(u0),'stationarity':sigma,'gradient_norm':float(np.linalg.norm(g)),'trust_radius':float(trust_radius)}
        history.append(hist)
        if sigma<=float(cfg['stationarity_max']): reason='stationarity_reached'; optimizer_resolved=True; break
        ls=_line_search(U,project,g,u0,initial_clear,initial_links,cfg,trust_radius)
        hist.update({'descent_qualification':{k:v for k,v in ls.items() if k not in ('trial','topology_proxy')},'accepted_step':ls.get('step'),'backtracks':ls.get('backtracks')})
        if ls.get('topology_proxy') is not None: hist['topology_proxy']=ls['topology_proxy']
        if ls['accepted']:
            cs=ls['trial']; hist['trial_energy']=float(ls['energy'])
            if int(ls.get('backtracks',0))==0:
                trust_radius=min(float(cfg['step0']),float(ls['step'])*float(cfg.get('trust_expand',1.5)))
            else:
                trust_radius=max(float(cfg.get('min_step',1e-7)),float(ls['step']))
            continue
        reason=ls['reason']; optimizer_resolved=bool(ls['numerically_resolved']); break
    if initial_energy is None:
        initial_energy=source_energy_before_objective

    # Rebuild the identical constrained objective at the endpoint.  The base state
    # returned by the factory is the geometry on which U_c(0), derivatives and
    # descriptors are all defined.
    U,project,B,offs,base=constrained_potential_factory(cs,core,modes,counts);cs=base
    uf,gf,K,hs=gradient_hessian_sweep(
        U,len(B),eps,
        negative_relative_tolerance=float(cfg['hessian_negative_relative_tolerance']),
        rel_l2_max=float(cfg.get('hessian_fd_rel_l2_max',0.15)),
    )
    sigmaf=float(np.linalg.norm(gf)/max(abs(uf),1e-12)); stationary=bool(sigmaf<=float(cfg['stationarity_max']))
    if stationary: optimizer_resolved=True
    topo=topology_proxy(initial_clear,initial_links,cs,float(cfg['clearance_retention']),float(cfg['link_drift_max']))
    eig=np.linalg.eigvalsh(.5*(K+K.T)); hessian_converged=bool(hs.get('converged'))
    nonnegative=bool(hs.get('authoritative_sign_class')=='NONNEGATIVE')
    stable=bool(stationary and hessian_converged and nonnegative)
    if stable:
        ring=mode_ringdown(U,K,float(cfg['ringdown_perturb_eps']),float(cfg['ringdown_dt']),int(cfg['ringdown_steps']))
    elif stationary and not hessian_converged:
        ring={'evaluated':False,'reason':'hessian_fd_unresolved'}
    else:
        ring={'evaluated':False,'reason':'endpoint_not_stationary_stable_candidate'}
    ring_bounded=bool(ring.get('evaluated') and ring.get('amplitude_ratio',float('inf'))<=float(cfg['ringdown_amplitude_ratio_max']) and ring.get('hamiltonian_relative_drift',float('inf'))<=float(cfg['ringdown_energy_drift_max']))
    final_desc=descriptors(cs)
    objective_match=abs(float(U(np.zeros(len(B))))-float(uf)) <= (float(cfg.get('objective_abs_tolerance',1e-10))+float(cfg.get('objective_rel_tolerance',1e-10))*max(1.0,abs(float(uf))))
    return {
      'components':cs,
      'source_reach':source_reach,
      'objective':'U_c(q)=H(N[R(X+deltaX(q))])',
      'source_energy_before_objective_projection':source_energy_before_objective,
      'initial_energy':float(initial_energy),'final_energy':float(uf),'energy_relative_change':float((uf-initial_energy)/max(abs(initial_energy),1e-30)),
      'initial_descriptors':initial_desc,'final_descriptors':final_desc,
      'initial_clearance':initial_clear,'initial_linking':initial_links,'topology_proxy':topo,
      'final_gradient_norm':float(np.linalg.norm(gf)),'final_stationarity':sigmaf,'stationarity_threshold':float(cfg['stationarity_max']),
      'stationary':stationary,'optimizer_numerically_resolved':bool(optimizer_resolved),'numerical_status':'RESOLVED' if optimizer_resolved else 'UNRESOLVED_NUMERICAL',
      'hessian_eigenvalues':eig.tolist(),'hessian_symmetry_rel':float(np.linalg.norm(K-K.T)/max(np.linalg.norm(K),1e-30)),
      'hessian_fd_sweep':hs,'hessian_fd_converged':hessian_converged,'hessian_sign_class':hs.get('authoritative_sign_class'),
      'stability_numerically_resolved':bool(stationary and hessian_converged),
      'stable_candidate':stable,'ringdown':ring,'ringdown_bounded':ring_bounded,
      'objective_consistency_verified':bool(objective_match),
      'termination_reason':reason,'iterations_recorded':len(history),'history':history,
    }
