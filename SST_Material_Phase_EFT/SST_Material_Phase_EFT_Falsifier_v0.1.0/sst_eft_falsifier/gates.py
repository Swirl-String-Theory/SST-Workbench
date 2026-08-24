import numpy as np
from .geometry import resample_arclength,observables,distorted_reparameterization,estimate_thickness,scale_to_core_units
from .bishop import gauge_invariance_residual,holonomy_convergence,wrapped_angle_diff
from .operators import redundancy_residuals,local_operator_vector
from .dynamics import run_mode,fit_dispersion

def _rel(a,b,floor=1e-14): return abs(a-b)/max(abs(a),abs(b),floor)
def gate_reparameterization(x,cfg):
    n=int(cfg.get('n_points',128)); base=resample_arclength(x,n); variants={'cyclic':np.roll(base,n//7,axis=0),'reverse':base[::-1].copy(),'distorted':distorted_reparameterization(base)}; ob=observables(base); keys=['length','ropelength','int_kappa2','writhe']; errs={}
    for name,y in variants.items():
        oy=observables(resample_arclength(y,n)); vals=[_rel(ob[k],oy[k]) for k in keys if np.isfinite(ob[k]) and np.isfinite(oy[k])]; errs[name]=max(vals) if vals else float('nan')
    worst=max(v for v in errs.values() if np.isfinite(v)); tol=float(cfg.get('reparam_rel_tol',.08)); return {'status':'PASS' if worst<=tol else 'FAIL','metric':worst,'threshold':tol,'details':errs,'observables':ob}
def gate_phase(x,cfg):
    n=int(cfg.get('n_points',128)); y=resample_arclength(x,n); gres,H=gauge_invariance_residual(y); n2=int(cfg.get('holonomy_n2',min(2*n,512))); h1,h2,conv=holonomy_convergence(x,n,n2); tg=float(cfg.get('gauge_tol_rad',1e-10)); th=float(cfg.get('holonomy_conv_tol_rad',.05)); physical='UNTESTED'; lr=None
    if cfg.get('phase_lock_target')=='integer_2pi': lr=abs(wrapped_angle_diff(h2,0.0)); physical='PASS' if lr<=float(cfg.get('phase_lock_tol_rad',.1)) else 'FAIL'
    return {'status':'PASS' if gres<=tg and conv<=th else 'FAIL','metric':max(gres,conv),'threshold':max(tg,th),'gauge_residual_rad':gres,'holonomy_n_rad':h1,'holonomy_n2_rad':h2,'holonomy_conv_rad':conv,'physical_phase_lock_status':physical,'phase_lock_residual_rad':lr,'note':'Static centerlines test candidate geometric phase consistency; they do not measure a physical SST phase clock.'}
def gate_redundancy(x,cfg):
    y=resample_arclength(x,int(cfg.get('n_points',128))); r=redundancy_residuals(y); worst=max(r.values()); tol=float(cfg.get('operator_identity_tol',.03)); return {'status':'PASS' if worst<=tol else 'FAIL','metric':worst,'threshold':tol,'details':r,'operators':local_operator_vector(y),'note':'Total-derivative/IBP gate only; full EOM/field-redefinition redundancy needs an explicit leading SST action.'}
def gate_dynamics(x,cfg):
    if not cfg.get('enabled',True): return {'status':'SKIP','mode_rows':[],'dispersion':{'status':'DISABLED'}}
    y=resample_arclength(x,int(cfg.get('n_points',128))); th=float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]; yc,_=scale_to_core_units(y,th); rows=[run_mode(yc,int(m),cfg) for m in cfg.get('modes',[2,3,4])]; disp=fit_dispersion(rows,float(cfg.get('min_phase_r2',.8))); tol=float(cfg.get('dispersion_rel_rmse_max',.3));
    if disp.get('status')!='OK': return {'status':'SKIP','metric':None,'threshold':tol,'mode_rows':rows,'dispersion':disp,'core_radius_coord_used':th,'note':'INCONCLUSIVE: too few usable projected modes. Regularized finite-core Biot-Savart closure; not full Euler and not the entire SST canon.'}
    metric=float(disp['rel_rmse']); return {'status':'PASS' if metric<=tol else 'FAIL','metric':metric,'threshold':tol,'mode_rows':rows,'dispersion':disp,'core_radius_coord_used':th,'note':'Regularized finite-core Biot-Savart closure; not full Euler and not the entire SST canon.'}
def temporal_convergence(x,cfg):
    if not cfg.get('enabled',False): return {'status':'SKIP'}
    y=resample_arclength(x,int(cfg.get('n_points',128))); th=float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]; yc,_=scale_to_core_units(y,th); m=int(cfg.get('mode',3)); a=run_mode(yc,m,cfg,1.0); b=run_mode(yc,m,cfg,.5)
    if not(np.isfinite(a['omega_core']) and np.isfinite(b['omega_core'])): return {'status':'FAIL','relative_error':float('inf'),'coarse':a,'fine':b}
    e=_rel(a['omega_core'],b['omega_core']); tol=float(cfg.get('rel_tol',.12)); return {'status':'PASS' if e<=tol else 'FAIL','relative_error':e,'threshold':tol,'coarse':a,'fine':b}
def spatial_convergence(x,cfg):
    if not cfg.get('enabled',False): return {'status':'SKIP'}
    rows=[]; m=int(cfg.get('mode',3))
    for n in cfg.get('resolutions',[96,128,160]):
        local=dict(cfg); local['n_points']=int(n); y=resample_arclength(x,int(n)); th=float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]; yc,_=scale_to_core_units(y,th); rows.append(run_mode(yc,m,local))
    good=[r for r in rows if np.isfinite(r['omega_core'])]
    if len(good)<2: return {'status':'FAIL','relative_error':float('inf'),'rows':rows}
    e=_rel(good[-1]['omega_core'],good[-2]['omega_core']); tol=float(cfg.get('rel_tol',.15)); return {'status':'PASS' if e<=tol else 'FAIL','relative_error':e,'threshold':tol,'rows':rows}
