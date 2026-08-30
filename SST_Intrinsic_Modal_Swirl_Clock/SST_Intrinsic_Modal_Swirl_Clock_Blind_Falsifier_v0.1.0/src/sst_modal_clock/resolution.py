from pathlib import Path
import csv,json,numpy as np

def _candidates(work):
    p=Path(work)/'analysis/blind_modal_results.csv'
    if not p.exists(): return {}
    out={}
    with open(p,newline='',encoding='utf-8') as f:
        for r in csv.DictReader(f):
            if str(r.get('clock_candidate','')).lower() not in ('true','1','yes'): continue
            cid=r['carrier_id']; score=float(r.get('material_clock_score') or 0)
            if cid not in out or score>out[cid][0]:
                def num(k):
                    try:return float(r.get(k,''))
                    except:return float('nan')
                out[cid]=(score,{'period':num('material_period'),'delay':num('stretch_delay'),'mode_index':int(r.get('mode_index') or 0)})
    return {k:v[1] for k,v in out.items()}

def compare(works,out):
    cs=[_candidates(w) for w in works]; common=set(cs[0]) if cs else set()
    for c in cs[1:]: common &= set(c)
    rows=[]
    for cid in sorted(common):
        periods=np.array([c[cid]['period'] for c in cs],float); delays=np.array([c[cid]['delay'] for c in cs],float)
        def spread(a):
            a=a[np.isfinite(a)]; return float((a.max()-a.min())/max(abs(np.median(a)),1e-15)) if len(a)==3 else float('inf')
        ps,ds=spread(periods),spread(delays); ok=ps<=.20 and ds<=.25
        rows.append({'carrier_id':cid,'periods':periods.tolist(),'delays':delays.tolist(),'relative_period_spread':ps,'relative_delay_spread':ds,'resolution_converged':ok})
    conv=[r for r in rows if r['resolution_converged']]; r={'format':'SST-INTRINSIC-MODAL-RESOLUTION-1.0','candidate_counts':[len(c) for c in cs],'common_candidate_carriers':len(common),'converged_candidate_carriers':len(conv),'candidates':rows,'verdict':'PASS_RESOLUTION_PERSISTENT_CANDIDATE' if conv else 'FAIL_OR_INDETERMINATE_NO_PERSISTENT_CANDIDATE'}
    Path(out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8'); return r
