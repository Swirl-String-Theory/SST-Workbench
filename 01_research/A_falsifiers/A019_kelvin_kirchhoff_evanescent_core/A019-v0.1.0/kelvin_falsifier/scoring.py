from __future__ import annotations
import math
from pathlib import Path
from .io import read_json,write_json

PASS='PASS'; FAIL='FAIL'; INC='INCONCLUSIVE'; NT='NOT_TESTABLE'
def _relerr(x,target): return abs(x-target)/max(abs(target),1e-300)

def score_case(raw, gates):
    if raw.get('status')=='ERROR': return {'overall':INC,'reason':'NUMERICAL_ERROR','gates':{}}
    g={}; geo=gates['geometry_qc']; reasons=[]
    if raw.get('core_radius_provenance')!='RIDGERUNNER_METRICS': reasons.append('core_radius_not_from_metrics')
    rr=raw.get('rr_residual'); recv=raw.get('resampled_edge_cv')
    if rr is not None and float(rr)>geo['max_ridgerunner_residual']: reasons.append('ridgerunner_residual')
    if recv is None or float(recv)>geo['max_resampled_edge_cv']: reasons.append('resampled_edge_cv')
    geo_ok=not reasons
    g['geometry_qc']={'status':PASS if geo_ok else FAIL,'reasons':reasons}

    re=raw['relative_equilibrium']['relative_residual']; th=gates['relative_equilibrium']['max_relative_residual']
    if not geo_ok:
        g['relative_equilibrium']={'status':INC,'reason':'GEOMETRY_QC_FAILED','diagnostic_relative_residual':re,'threshold':th}
        re_ok=False
    else:
        re_ok=re<=th; g['relative_equilibrium']={'status':PASS if re_ok else FAIL,'relative_residual':re,'threshold':th}

    d=raw.get('dispersion',{}); kg=gates['kelvin_gap']; kreasons=[]
    if not geo_ok:
        g['kelvin_2omega_gap']={'status':INC,'reason':'GEOMETRY_QC_FAILED','diagnostic_ratio':d.get('gap_to_2omega_ratio')}
    elif not re_ok:
        g['kelvin_2omega_gap']={'status':INC,'reason':'BASE_STATE_NOT_RELATIVE_EQUILIBRIUM','diagnostic_ratio':d.get('gap_to_2omega_ratio')}
    elif d.get('status')!='OK':
        g['kelvin_2omega_gap']={'status':INC,'reason':d.get('status','NO_DISPERSION')}
    else:
        ratio=d.get('gap_to_2omega_ratio')
        if ratio is None or not math.isfinite(ratio): kreasons.append('invalid_gap_ratio')
        elif _relerr(ratio,1.0)>kg['max_relative_error_gap_ratio']: kreasons.append('gap_not_2omega')
        if d.get('train_r2',-1)<kg['min_train_r2']: kreasons.append('poor_train_r2')
        if d.get('holdout_nrmse',999)>kg['max_holdout_nrmse']: kreasons.append('poor_holdout_prediction')
        if d.get('delta_aic_zero_minus_gap',-999)<kg['min_delta_aic_gap_over_zero']: kreasons.append('gap_model_not_preferred')
        if d.get('slope',-1)<=0: kreasons.append('nonpositive_wave_slope')
        g['kelvin_2omega_gap']={'status':PASS if not kreasons else FAIL,'reasons':kreasons,'ratio':ratio,'train_r2':d.get('train_r2'),'holdout_nrmse':d.get('holdout_nrmse'),'delta_aic':d.get('delta_aic_zero_minus_gap')}

    r=raw.get('radial_response',{}); eg=gates['evanescent_confinement']; ereasons=[]
    if not geo_ok:
        g['evanescent_confinement']={'status':INC,'reason':'GEOMETRY_QC_FAILED'}
    elif not re_ok:
        g['evanescent_confinement']={'status':INC,'reason':'BASE_STATE_NOT_RELATIVE_EQUILIBRIUM'}
    elif r.get('status')!='OK':
        g['evanescent_confinement']={'status':INC,'reason':r.get('status','NO_RADIAL_RESPONSE')}
    else:
        lr=r.get('length_ratio')
        if lr is None or not math.isfinite(lr): ereasons.append('invalid_length_ratio')
        elif _relerr(lr,1.0)>eg['max_relative_error_length_ratio']: ereasons.append('decay_length_mismatch')
        if r.get('exp_log_r2',-1)<eg['min_exp_log_r2']: ereasons.append('poor_exponential_fit')
        if r.get('delta_aic_power_minus_exp',-999)<eg['min_delta_aic_exp_over_power']: ereasons.append('exponential_not_preferred_to_power')
        g['evanescent_confinement']={'status':PASS if not ereasons else FAIL,'reasons':ereasons,'length_ratio':lr,'exp_log_r2':r.get('exp_log_r2'),'delta_aic':r.get('delta_aic_power_minus_exp')}

    g['kirchhoff_detailed_balance']={'status':NT,'reason':'CENTERLINE_ONLY_DATA_HAVE_NO_MODE_RESOLVED_EQUILIBRIUM INCIDENT/ABSORBED/EMITTED FLUXES; NO PROXY IS SUBSTITUTED'}
    if not geo_ok:
        overall=INC
    else:
        physical=[g[k]['status'] for k in ['relative_equilibrium','kelvin_2omega_gap','evanescent_confinement']]
        overall=FAIL if FAIL in physical else (PASS if all(x==PASS for x in physical) else INC)
    return {'overall':overall,'gates':g}

def score_blind(blind_dir: str|Path):
    blind=Path(blind_dir); results=blind/'results'; prereg=read_json(results/'frozen_preregistration.json'); manifest=read_json(blind/'blind_manifest.json')
    out=[]
    for c in manifest['cases']:
        cid=c['case_id']; raw=read_json(results/cid/'raw.json'); score=score_case(raw,prereg)
        score['case_id']=cid; write_json(results/cid/'score.json',score); out.append(score)
    write_json(results/'blind_scores.json',out); return out
