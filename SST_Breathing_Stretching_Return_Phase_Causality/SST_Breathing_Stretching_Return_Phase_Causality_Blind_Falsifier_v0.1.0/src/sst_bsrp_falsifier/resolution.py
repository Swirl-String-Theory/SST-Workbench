from pathlib import Path
import csv, json, math
import numpy as np
from .util import clean_json

def _rows(path):
    out={}
    with open(path,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if str(r.get('valid','')).lower() not in ('true','1'): continue
            out[r['pair_id']]=r
    return out

def _f(r,k):
    try: return float(r[k])
    except Exception: return float('nan')

def _circ(a,b):
    return abs(float(np.angle(np.exp(1j*(a-b)))))

def compare(root64,root96,root128,outpath):
    A=_rows(Path(root64)/'results/blind_pair_results.csv')
    B=_rows(Path(root96)/'results/blind_pair_results.csv')
    C=_rows(Path(root128)/'results/blind_pair_results.csv')
    keys=sorted(set(A)&set(B)&set(C))
    rec=[]
    for k in keys:
        a,b,c=A[k],B[k],C[k]
        t64,t96,t128=_f(a,'tau_return'),_f(b,'tau_return'),_f(c,'tau_return')
        p64,p96,p128=_f(a,'return_phase_rad'),_f(b,'return_phase_rad'),_f(c,'return_phase_rad')
        y64,y96,y128=_f(a,'restoring_response'),_f(b,'restoring_response'),_f(c,'restoring_response')
        vals=[t64,t96,t128,p64,p96,p128,y64,y96,y128]
        if not np.isfinite(vals).all(): continue
        rec.append({
            'pair_id':k,
            'tau_rel_64_96':abs(t96-t64)/max(abs(t96),1e-15),
            'tau_rel_96_128':abs(t128-t96)/max(abs(t128),1e-15),
            'phase_abs_64_96_rad':_circ(p64,p96),
            'phase_abs_96_128_rad':_circ(p96,p128),
            'response_rel_64_96':abs(y96-y64)/(abs(y96)+abs(y64)+1e-15)*2,
            'response_rel_96_128':abs(y128-y96)/(abs(y128)+abs(y96)+1e-15)*2,
        })
    def med(k): return float(np.median([r[k] for r in rec])) if rec else float('nan')
    s={
      'format':'SST-BSRP-RESOLUTION-1.0','n_shared_valid_pairs':len(rec),
      'median_tau_rel_64_96':med('tau_rel_64_96'),'median_tau_rel_96_128':med('tau_rel_96_128'),
      'median_phase_abs_64_96_rad':med('phase_abs_64_96_rad'),'median_phase_abs_96_128_rad':med('phase_abs_96_128_rad'),
      'median_response_rel_64_96':med('response_rel_64_96'),'median_response_rel_96_128':med('response_rel_96_128')}
    if len(rec)>=4:
        s['resolution_gate']='PASS' if (s['median_tau_rel_96_128']<=.10 and s['median_phase_abs_96_128_rad']<=.25 and s['median_response_rel_96_128']<=.25) else 'FAIL'
    else: s['resolution_gate']='INDETERMINATE_INSUFFICIENT_SHARED_PAIRS'
    Path(outpath).parent.mkdir(parents=True,exist_ok=True)
    Path(outpath).write_text(json.dumps(clean_json(s),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    return s
