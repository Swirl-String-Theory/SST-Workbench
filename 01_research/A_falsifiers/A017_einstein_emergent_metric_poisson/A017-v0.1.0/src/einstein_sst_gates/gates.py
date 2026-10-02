from __future__ import annotations
import numpy as np, pandas as pd

def state(ok): return 'PASS' if bool(ok) else 'FAIL'
def evaluate_row(row,cfg):
    g=cfg['gates']; out={'blind_id':row['blind_id']}
    if row.get('status')!='OK': out['overall']='NOT_TESTED';out['reason']='measurement error';return out
    statuses=[]
    # Primary gate 1: Einstein/Newton direct mapping Phi=-v^2/2 requires v^2 ~ 1/r.
    e=abs(float(row['tail_v2_exponent'])-1.0); s=state(e<=float(g['v2_exponent_abs_error_max']));out['monopole_1_over_r']=s;out['v2_exponent_abs_error']=e;statuses.append(s)
    s2=state(abs(float(row['tail_mu_amp_log_slope']))<=float(g['mu_plateau_log_slope_abs_max']));out['monopole_plateau']=s2;statuses.append(s2)
    # Primary gate 2: pressure-Poisson integral must asymptote to a nonzero 4pi*mu and agree with Phi-derived mu.
    slope=abs(float(row['tail_mu_poisson_log_slope'])); ratio=float(row['tail_poisson_to_amp_ratio']); sign=float(row['tail_poisson_positive_fraction'])
    ratio_ok=np.isfinite(ratio) and ratio>0 and abs(np.log(abs(ratio)))<=float(g['poisson_to_amp_log_ratio_abs_max'])
    s3=state(slope<=float(g['poisson_mu_log_slope_abs_max']) and ratio_ok and sign>=float(g['poisson_positive_fraction_min']));out['pressure_poisson_monopole']=s3;statuses.append(s3)
    # Secondary closure: Phi=-v^2/2 and pressure closure surface integrals agree.
    rpf=float(row['tail_poisson_to_phi_ratio']); ok=np.isfinite(rpf) and rpf>0 and abs(np.log(abs(rpf)))<=float(g['poisson_to_phi_log_ratio_abs_max']); s4=state(ok);out['pressure_phi_closure']=s4;statuses.append(s4)
    # Secondary isotropy / Beltrami diagnostics are reported but not required for the two headline gates unless configured.
    out['tail_isotropy']=state(float(row['tail_anisotropy_median'])<=float(g['tail_v2_cv_max']))
    out['beltrami_closure']=state(float(row['tail_beltrami_misalignment_median'])<=float(g['beltrami_misalignment_max']))
    out['overall']='FAIL' if 'FAIL' in statuses else ('PASS' if statuses and all(x=='PASS' for x in statuses) else 'NOT_TESTED')
    return out

def reveal(df,cfg):
    rdf=pd.DataFrame([evaluate_row(r,cfg) for _,r in df.iterrows()]) if len(df) else pd.DataFrame()
    if not len(rdf): return rdf,'NOT_TESTED'
    vals=list(rdf['overall'])
    overall='FAIL' if 'FAIL' in vals else ('PASS' if vals and all(v=='PASS' for v in vals) else 'NOT_TESTED')
    return rdf,overall
