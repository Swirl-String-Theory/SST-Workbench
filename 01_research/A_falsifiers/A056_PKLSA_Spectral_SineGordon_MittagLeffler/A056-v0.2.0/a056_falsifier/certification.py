from __future__ import annotations
import numpy as np
from .numeric import phase_features, phase_feature_parity, ml_backend_parity
from .models import phase_model_competition, ringdown_competition

def phase_resolution_certification(phi,dt,ds,boundary,cfg):
    y,ss,p=phase_features(phi,dt,ds,boundary,'python'); full=phase_model_competition(y,ss,p,cfg['phase']['discovery_fraction'])['SG']
    coarse=np.asarray(phi)[::2,::2]
    if min(coarse.shape)<8: return {"pass":False,"reason":"coarse grid too small"}
    yc,ssc,pc=phase_features(coarse,dt*2,ds*2,boundary,'python'); crs=phase_model_competition(yc,ssc,pc,cfg['phase']['discovery_fraction'])['SG']
    fc=np.asarray(full['coef'][:2],float); cc=np.asarray(crs['coef'][:2],float)
    rel=float(np.linalg.norm(fc-cc)/max(np.linalg.norm(fc),1e-30))
    return {"pass":rel<=cfg['numerics']['phase_resolution_relative_max'],"sg_coeff_relative_l2":rel,
            "full_coef":fc.tolist(),"coarse_coef":cc.tolist()}

def memory_resolution_certification(t,y,cfg):
    full,_,_=ringdown_competition(t,y,cfg['ringdown']['train_fraction']); f=full['ML']
    tc=np.asarray(t)[::2]; yc=np.asarray(y)[::2]
    if len(tc)<12: return {"pass":False,"reason":"coarse ringdown too short"}
    coarse,_,_=ringdown_competition(tc,yc,cfg['ringdown']['train_fraction']); c=coarse['ML']
    da=abs(float(f['alpha'])-float(c['alpha'])); dtau=abs(float(f['tau'])-float(c['tau']))/max(abs(float(f['tau'])),1e-30)
    passed=da<=cfg['numerics']['memory_alpha_abs_max'] and dtau<=cfg['numerics']['memory_tau_relative_max']
    return {"pass":passed,"alpha_abs_delta":da,"tau_relative_delta":dtau,
            "full_alpha":f['alpha'],"coarse_alpha":c['alpha'],"full_tau":f['tau'],"coarse_tau":c['tau']}

def phase_backend_certification(phi,dt,ds,boundary,cfg):
    par=phase_feature_parity(phi,dt,ds,boundary)
    if not par['available']: return {**par,"pass":not cfg['numerics']['native_required'],"reason":"native unavailable"}
    return {**par,"pass":par['relative_l2']<=cfg['numerics']['native_parity_relative_max']}

def memory_backend_certification(t,tau,alpha,cfg):
    par=ml_backend_parity(t,tau,alpha)
    if not par['available']: return {**par,"pass":not cfg['numerics']['native_required'],"reason":"native unavailable"}
    return {**par,"pass":par['relative_l2']<=cfg['numerics']['native_parity_relative_max']}
