import numpy as np
from .geometry import align_cyclic,high_k_fraction,rigid_normal_fit,pod_fraction,resample_closed
from .solver import rhs


def aligned_series(traj,x0,coarse_stride=4,parameterization_invariant=True):
    ref=resample_closed(np.asarray(x0,float),len(x0)) if parameterization_invariant else np.asarray(x0,float)
    aligned=[]; d=[]; shifts=[]
    for x in traj['x']:
        y=resample_closed(np.asarray(x,float),len(ref)) if parameterization_invariant else np.asarray(x,float)
        a,di,sh,R,t=align_cyclic(y,ref,coarse_stride); aligned.append(a); d.append(di); shifts.append(sh)
    return np.asarray(aligned),np.asarray(d),np.asarray(shifts)


def shape_distance(a,b,coarse_stride=4):
    aa=resample_closed(np.asarray(a,float),len(b)); bb=resample_closed(np.asarray(b,float),len(b))
    _,d,_,_,_=align_cyclic(aa,bb,coarse_stride)
    return float(d)


def _pod_effective_rank(displacements):
    D=np.asarray(displacements,float)
    if D.ndim<3 or len(D)<2: return 0.0
    A=D.reshape(len(D),-1); A=A-A.mean(0,keepdims=True); s=np.linalg.svd(A,compute_uv=False); p=s*s
    if np.sum(p)<=1e-30: return 0.0
    q=p/np.sum(p); q=q[q>1e-30]
    return float(np.exp(-np.sum(q*np.log(q))))


def rolling_metrics(traj,x0,cfg):
    A,d,sh=aligned_series(traj,x0,int(cfg.get('cyclic_stride',4)),True)
    T=max(float(traj['t'][-1]),1e-15); auc=float(np.trapezoid(d,traj['t'])/T) if len(d)>1 else float(d[-1])
    ref=resample_closed(np.asarray(x0,float),len(x0)); disp=A-ref
    hk=float(np.median([high_k_fraction(z,cfg.get('high_k_cut_fraction',.33)) for z in disp[1:]])) if len(disp)>1 else 0.0
    pod=pod_fraction(disp[1:],int(cfg.get('pod_modes',3))); erank=_pod_effective_rank(disp[1:])
    u,_=rhs(ref,float(cfg.get('gamma',1.0)),float(cfg['core_fraction']),'fixed',bool(cfg.get('require_native',True)),ref_lengths=None,L0=float(np.sum(np.linalg.norm(np.roll(ref,-1,axis=0)-ref,axis=1))))
    rf=rigid_normal_fit(ref,u); scale=float(cfg.get('score_shape_scale',.12)); hk_scale=float(cfg.get('score_highk_scale',.12)); coh=rf['coherence']
    shape_term=float(np.exp(-auc/max(scale,1e-12))); hk_term=float(np.exp(-hk/max(hk_scale,1e-12)))
    mesh_term=float(np.exp(-float(np.max(traj['ds_cv']))/.25)); contact_term=1.0 if traj['stop_reason']=='COMPLETED' else 0.0
    # v0.2.0: POD dimensionality is diagnostic-only by default. Prior Q/H/P work showed
    # that useful early normal motion can live outside a preselected low-dimensional subspace.
    w=cfg.get('score_weights',{'rolling':.40,'shape':.30,'highk':.15,'pod':0.0,'contact':.10,'mesh':.05})
    score=float(w.get('rolling',0)*coh+w.get('shape',0)*shape_term+w.get('highk',0)*hk_term+w.get('pod',0)*pod+w.get('contact',0)*contact_term+w.get('mesh',0)*mesh_term)
    return {
        'score':score,'rolling_coherence':coh,'omega_mag':rf['omega_mag'],'translation_mag':rf['translation_mag'],
        'rigid_residual_rms':rf['residual_rms'],'shape_auc':auc,'shape_final':float(d[-1]),
        'shape_min_post_initial':float(np.min(d[1:])) if len(d)>1 else float(d[-1]),'high_k_median':hk,
        'pod_topk_fraction':pod,'pod_effective_rank':erank,'pod_is_diagnostic_only':bool(float(w.get('pod',0.0))==0.0),
        'max_ds_cv':float(np.max(traj['ds_cv'])),'min_gap_over_ds':float(np.min(traj['gap_over_ds'])),
        'max_mesh_ratio':float(np.max(traj.get('mesh_ratio',np.asarray([0.0])))),'stop_reason':traj['stop_reason'],
        'actual_t_final':float(traj['t'][-1]),'completed':bool(traj.get('completed',traj['stop_reason']=='COMPLETED')),
    }


def recurrence_metrics(traj,x0,cfg):
    A,d,sh=aligned_series(traj,x0,int(cfg.get('cyclic_stride',4)),True); t=np.asarray(traj['t'],float)
    tmin=float(cfg.get('return_min_time',.5)); actual=float(t[-1]) if len(t) else 0.0; target=float(traj.get('target_t_final',actual))
    base={
        'completed':bool(traj.get('completed',traj.get('stop_reason')=='COMPLETED')),
        'stop_reason':str(traj.get('stop_reason','UNKNOWN')),'actual_t_final':actual,'target_t_final':target,
        'observation_window_reached':bool(actual>=tmin),'best_return':float('inf'),'best_return_time':float('nan'),
        'n_returns':0,'period_cv':float('inf'),'return_times':[],'ds_cv_at_best_return':float('nan'),
        'gap_over_ds_at_best_return':float('nan'),
    }
    mask=t>=tmin
    if not np.any(mask):
        return base
    idx=np.where(mask)[0]; local=[]
    for i in idx:
        if i<=0 or i>=len(d)-1: continue
        if d[i]<=d[i-1] and d[i]<=d[i+1]: local.append(i)
    thr=float(cfg.get('return_threshold',.08)); good=[i for i in local if d[i]<=thr]
    j=int(idx[np.argmin(d[idx])]); times=np.asarray([t[i] for i in good]); periods=np.diff(times)
    pcv=float(np.std(periods)/max(np.mean(periods),1e-15)) if len(periods)>=2 else float('inf')
    base.update({
        'best_return':float(d[j]),'best_return_time':float(t[j]),'n_returns':len(good),'period_cv':pcv,
        'return_times':[float(t[i]) for i in good],
        'ds_cv_at_best_return':float(np.asarray(traj['ds_cv'])[j]) if j<len(traj['ds_cv']) else float('nan'),
        'gap_over_ds_at_best_return':float(np.asarray(traj['gap_over_ds'])[j]) if j<len(traj['gap_over_ds']) else float('nan'),
    })
    return base
