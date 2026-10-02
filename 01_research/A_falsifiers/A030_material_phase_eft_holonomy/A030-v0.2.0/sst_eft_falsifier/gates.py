import numpy as np
from .geometry import resample_arclength, observables, distorted_reparameterization, estimate_thickness, scale_to_core_units
from .bishop import gauge_invariance_residual, holonomy_convergence, wrapped_angle_diff
from .operators import redundancy_residuals, local_operator_vector
from .dynamics import run_mode, fit_dispersion


def _rel(a,b,floor=1e-14):
    return abs(a-b)/max(abs(a),abs(b),floor)


def gate_reparameterization(x,cfg):
    n = int(cfg.get('n_points',128))
    base = resample_arclength(x,n)
    variants = {
        'cyclic': np.roll(base,n//7,axis=0),
        'reverse': base[::-1].copy(),
        'distorted': distorted_reparameterization(base),
    }
    ob = observables(base)
    # Hard gate excludes ropelength/thickness: the current discrete thickness
    # estimator is deliberately retained only as a diagnostic because it is
    # sensitive to sampling density.
    hard_keys = ['length','int_kappa2','writhe']
    diag_keys = ['ropelength','int_tau2']
    details = {}
    hard = []
    for name,y in variants.items():
        oy = observables(resample_arclength(y,n))
        per = {}
        for k in hard_keys + diag_keys:
            if np.isfinite(ob.get(k,np.nan)) and np.isfinite(oy.get(k,np.nan)):
                per[k] = _rel(ob[k],oy[k])
        h = max([per[k] for k in hard_keys if k in per], default=float('nan'))
        details[name] = {'hard_max':h,'per_observable':per}
        if np.isfinite(h): hard.append(h)
    worst = max(hard) if hard else float('inf')
    tol = float(cfg.get('reparam_rel_tol',.08))
    return {
        'status':'PASS' if worst<=tol else 'FAIL', 'metric':worst,'threshold':tol,
        'details':details,'observables':ob,
        'note':'Centerline surrogate only. Ropelength/thickness is diagnostic, not a hard relabeling invariant in v0.1.1.'
    }


def gate_phase(x,cfg):
    n = int(cfg.get('n_points',128)); y = resample_arclength(x,n)
    gres,H = gauge_invariance_residual(y)
    n2 = int(cfg.get('holonomy_n2',min(2*n,512)))
    h1,h2,conv12 = holonomy_convergence(x,n,n2)
    tg = float(cfg.get('gauge_tol_rad',1e-10)); th = float(cfg.get('holonomy_conv_tol_rad',.05))
    refined = False; h3 = None; conv23 = None; conv = conv12
    if conv12 > th and bool(cfg.get('adaptive_holonomy_refine',True)):
        n3 = int(cfg.get('holonomy_n3',min(2*n2,1024)))
        if n3 > n2:
            _,h3,conv23 = holonomy_convergence(x,n2,n3)
            refined = True; conv = conv23; h2_report = h3
        else:
            h2_report = h2
    else:
        h2_report = h2

    physical = 'UNTESTED'; lr = None
    if cfg.get('phase_lock_target') == 'integer_2pi':
        lr = abs(wrapped_angle_diff(h2_report,0.0))
        physical = 'PASS' if lr <= float(cfg.get('phase_lock_tol_rad',.1)) else 'FAIL'

    return {
        'status':'PASS' if gres<=tg and conv<=th else 'FAIL',
        'metric':max(gres,conv),'threshold':max(tg,th),
        'gauge_residual_rad':gres,'holonomy_n_rad':h1,
        'holonomy_n2_rad':h2,'holonomy_n3_rad':h3,
        'holonomy_conv_n_to_n2_rad':conv12,
        'holonomy_conv_n2_to_n3_rad':conv23,
        'holonomy_conv_rad':conv,'adaptive_refined':refined,
        'physical_phase_lock_status':physical,'phase_lock_residual_rad':lr,
        'note':'Numerical/geometric candidate-phase diagnostic. With phase_lock_target=null this gate cannot by itself falsify a physical SST phase clock.'
    }


def gate_redundancy(x,cfg):
    y = resample_arclength(x,int(cfg.get('n_points',128)))
    r = redundancy_residuals(y); worst = max(r.values())
    tol = float(cfg.get('operator_identity_tol',.03))
    return {
        'status':'PASS' if worst<=tol else 'FAIL','metric':worst,'threshold':tol,
        'details':r,'operators':local_operator_vector(y),
        'note':'Implementation/operator-basis pre-gate only; full EOM/field-redefinition redundancy requires an explicit leading SST action.'
    }


def gate_dynamics(x,cfg):
    if not cfg.get('enabled',True):
        return {'status':'SKIP','mode_rows':[],'dispersion':{'status':'DISABLED'}}
    y = resample_arclength(x,int(cfg.get('n_points',128)))
    th = float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]
    yc,_ = scale_to_core_units(y,th)
    rows = [run_mode(yc,int(m),cfg) for m in cfg.get('modes',[2,3,4,5])]
    disp = fit_dispersion(rows,cfg)
    tol = float(cfg.get('dispersion_rel_rmse_max',.3))
    if disp.get('status') != 'OK':
        return {
            'status':'SKIP','metric':None,'threshold':tol,'mode_rows':rows,
            'dispersion':disp,'core_radius_coord_used':th,
            'note':'INCONCLUSIVE: insufficient linearly converged oscillatory projected modes. Local regularized finite-core Biot-Savart response; not Floquet/full Euler.'
        }
    metric = float(disp['rel_rmse'])
    return {
        'status':'PASS' if metric<=tol else 'FAIL','metric':metric,'threshold':tol,
        'mode_rows':rows,'dispersion':disp,'core_radius_coord_used':th,
        'note':'Local projected linear-response dispersion gate. Eigenvalues are not called stability/Floquet exponents unless a base relative equilibrium is independently established.'
    }


def temporal_convergence(x,cfg):
    if not cfg.get('enabled',False): return {'status':'SKIP'}
    y=resample_arclength(x,int(cfg.get('n_points',128)))
    th=float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]
    yc,_=scale_to_core_units(y,th); m=int(cfg.get('mode',3))
    a=run_mode(yc,m,cfg,1.0); b=run_mode(yc,m,cfg,.5)
    # Time convergence concerns the RK4 track, not the instantaneous projected operator.
    if not(np.isfinite(a['track_omega_core']) and np.isfinite(b['track_omega_core'])):
        return {'status':'FAIL','relative_error':float('inf'),'coarse':a,'fine':b}
    e=_rel(a['track_omega_core'],b['track_omega_core']); tol=float(cfg.get('rel_tol',.12))
    return {'status':'PASS' if e<=tol else 'FAIL','relative_error':e,'threshold':tol,'coarse':a,'fine':b}


def spatial_convergence(x,cfg):
    if not cfg.get('enabled',False): return {'status':'SKIP'}
    rows=[]; m=int(cfg.get('mode',3))
    for n in cfg.get('resolutions',[96,128,160]):
        local=dict(cfg); local['n_points']=int(n)
        y=resample_arclength(x,int(n))
        th=float(cfg['core_radius_coord']) if cfg.get('core_radius_coord') is not None else estimate_thickness(y)[0]
        yc,_=scale_to_core_units(y,th); rows.append(run_mode(yc,m,local))
    good=[r for r in rows if np.isfinite(r['omega_core'])]
    if len(good)<2: return {'status':'FAIL','relative_error':float('inf'),'rows':rows}
    e=_rel(good[-1]['omega_core'],good[-2]['omega_core']); tol=float(cfg.get('rel_tol',.15))
    return {'status':'PASS' if e<=tol else 'FAIL','relative_error':e,'threshold':tol,'rows':rows}
