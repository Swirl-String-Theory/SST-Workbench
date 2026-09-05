import numpy as np
from .geometry import align_cyclic,high_k_fraction,rigid_normal_fit,pod_fraction
from .solver import rhs

def aligned_series(traj,x0,coarse_stride=4):
    aligned=[]; d=[]; shifts=[]
    for x in traj['x']:
        a,di,sh,R,t=align_cyclic(x,x0,coarse_stride); aligned.append(a); d.append(di); shifts.append(sh)
    return np.asarray(aligned),np.asarray(d),np.asarray(shifts)

def rolling_metrics(traj,x0,cfg):
    A,d,sh=aligned_series(traj,x0,int(cfg.get('cyclic_stride',4))); T=max(float(traj['t'][-1]),1e-15); auc=float(np.trapezoid(d,traj['t'])/T) if len(d)>1 else float(d[-1]); disp=A-x0; hk=float(np.median([high_k_fraction(z,cfg.get('high_k_cut_fraction',.33)) for z in disp[1:]])) if len(disp)>1 else 0.0; pod=pod_fraction(disp[1:],int(cfg.get('pod_modes',3)))
    # initial physical normal rigid-body coherence
    u,_=rhs(x0,float(cfg.get('gamma',1.0)),float(cfg['core_fraction']),'fixed',bool(cfg.get('require_native',True)),ref_lengths=None,L0=float(np.sum(np.linalg.norm(np.roll(x0,-1,axis=0)-x0,axis=1))))
    rf=rigid_normal_fit(x0,u); scale=float(cfg.get('score_shape_scale',.12)); hk_scale=float(cfg.get('score_highk_scale',.12)); coh=rf['coherence']; shape_term=float(np.exp(-auc/max(scale,1e-12))); hk_term=float(np.exp(-hk/max(hk_scale,1e-12))); mesh_term=float(np.exp(-float(np.max(traj['ds_cv']))/.25)); contact_term=1.0 if traj['stop_reason']=='COMPLETED' else 0.0
    w=cfg.get('score_weights',{'rolling':.35,'shape':.25,'highk':.15,'pod':.10,'contact':.10,'mesh':.05}); score=float(w['rolling']*coh+w['shape']*shape_term+w['highk']*hk_term+w['pod']*pod+w['contact']*contact_term+w['mesh']*mesh_term)
    return {'score':score,'rolling_coherence':coh,'omega_mag':rf['omega_mag'],'translation_mag':rf['translation_mag'],'rigid_residual_rms':rf['residual_rms'],'shape_auc':auc,'shape_final':float(d[-1]),'shape_min_post_initial':float(np.min(d[1:])) if len(d)>1 else float(d[-1]),'high_k_median':hk,'pod_topk_fraction':pod,'max_ds_cv':float(np.max(traj['ds_cv'])),'min_gap_over_ds':float(np.min(traj['gap_over_ds'])),'stop_reason':traj['stop_reason'],'actual_t_final':float(traj['t'][-1])}

def recurrence_metrics(traj,x0,cfg):
    A,d,sh=aligned_series(traj,x0,int(cfg.get('cyclic_stride',4))); t=traj['t']; tmin=float(cfg.get('return_min_time',.5)); mask=t>=tmin
    if not np.any(mask): return {'best_return':float('inf'),'best_return_time':float('nan'),'n_returns':0,'period_cv':float('inf')}
    idx=np.where(mask)[0]; local=[]
    for i in idx:
        if i<=0 or i>=len(d)-1: continue
        if d[i]<=d[i-1] and d[i]<=d[i+1]: local.append(i)
    thr=float(cfg.get('return_threshold',.08)); good=[i for i in local if d[i]<=thr]
    j=idx[np.argmin(d[idx])]; times=np.asarray([t[i] for i in good])
    periods=np.diff(times); pcv=float(np.std(periods)/max(np.mean(periods),1e-15)) if len(periods)>=2 else float('inf')
    return {'best_return':float(d[j]),'best_return_time':float(t[j]),'n_returns':len(good),'period_cv':pcv,'return_times':[float(t[i]) for i in good],'completed':traj['stop_reason']=='COMPLETED'}
