from pathlib import Path
import csv,json
import numpy as np
from .util import clean_json

def _summary(work):
    return json.loads((Path(work)/'results/blind_summary.json').read_text(encoding='utf-8'))

def _rows(work):
    out={}
    p=Path(work)/'results/blind_pair_results.csv'
    with open(p,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if str(r.get('valid','')).lower() in ('true','1'):
                out[r['pair_id']]=r
    return out

def _float(x,default=np.nan):
    try:return float(x)
    except Exception:return default

def compare(material_work,fixed_work,outpath):
    m=_summary(material_work); f=_summary(fixed_work); rm=_rows(material_work); rf=_rows(fixed_work)
    common=sorted(set(rm)&set(rf)); ratios=[]; diffs=[]
    for k in common:
        ym=_float(rm[k].get('restoring_response')); yf=_float(rf[k].get('restoring_response'))
        if np.isfinite(ym) and np.isfinite(yf):
            ratios.append(abs(ym)/(abs(yf)+1e-15)); diffs.append(abs(ym-yf)/(abs(ym)+abs(yf)+1e-15)*2)
    mcv=_float(m.get('loco_cv_r2')); fcv=_float(f.get('loco_cv_r2'))
    delta=mcv-fcv if np.isfinite(mcv) and np.isfinite(fcv) else np.nan
    out={
      'format':'SST-BSRP-STRETCH-MEDIATION-1.0',
      'material_core_exponent':-0.5,'fixed_core_exponent':0.0,
      'material_primary_gate':m.get('primary_phase_causality_gate'),
      'fixed_core_primary_gate':f.get('primary_phase_causality_gate'),
      'material_loco_cv_r2':mcv,'fixed_core_loco_cv_r2':fcv,
      'material_minus_fixed_cv_r2':delta,
      'n_common_valid_pairs':len(ratios),
      'median_abs_response_ratio_material_over_fixed':float(np.median(ratios)) if ratios else None,
      'median_symmetric_response_difference':float(np.median(diffs)) if diffs else None,
    }
    if m.get('primary_phase_causality_gate')!='PASS':
        out['stretch_mediation_gate']='FAIL_MATERIAL_BRANCH_NOT_CONFIRMED' if str(m.get('primary_phase_causality_gate','')).startswith('FAIL') else 'INDETERMINATE_MATERIAL_BRANCH'
    elif len(ratios)<6 or not np.isfinite(delta):
        out['stretch_mediation_gate']='INDETERMINATE_INSUFFICIENT_MATCHED_NULL_DATA'
    elif f.get('primary_phase_causality_gate')=='PASS':
        out['stretch_mediation_gate']='FAIL_EFFECT_NOT_SPECIFIC_TO_STRETCH_CORE_FEEDBACK'
    elif delta < .05:
        out['stretch_mediation_gate']='FAIL_MATERIAL_BRANCH_DOES_NOT_OUTPERFORM_FIXED_CORE_NULL'
    else:
        out['stretch_mediation_gate']='PASS'
    Path(outpath).parent.mkdir(parents=True,exist_ok=True)
    Path(outpath).write_text(json.dumps(clean_json(out),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    return out
