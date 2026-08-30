from pathlib import Path
import json,numpy as np

def _candidates(work):
    p=Path(work)/'analysis/stage_a_candidates.json'
    if not p.exists(): return {}
    data=json.loads(p.read_text(encoding='utf-8')); out={}
    for r in data.get('candidates',[]):
        key=(r['carrier_id'],r['channel']); score=float(r.get('discovery_energy_fraction') or 0)
        if key not in out or score>out[key][0]:
            out[key]=(score,{'period':float(r.get('period',np.nan)),'closure':float(r.get('closure_median',np.nan)),'period_cv':float(r.get('period_cv',np.nan)),'mode_index':int(r.get('mode_index',0))})
    return {k:v[1] for k,v in out.items()}

def compare(works,out):
    cs=[_candidates(w) for w in works]; common=set(cs[0]) if cs else set()
    for c in cs[1:]: common &= set(c)
    rows=[]
    for key in sorted(common):
        periods=np.array([c[key]['period'] for c in cs],float); closures=np.array([c[key]['closure'] for c in cs],float)
        def spread(a):
            a=a[np.isfinite(a)]; return float((a.max()-a.min())/max(abs(np.median(a)),1e-15)) if len(a)==3 else float('inf')
        ps=spread(periods); cspr=spread(closures); ok=ps<=.20 and cspr<=.35
        rows.append({'carrier_id':key[0],'channel':key[1],'periods':periods.tolist(),'closures':closures.tolist(),'relative_period_spread':ps,'relative_closure_spread':cspr,'resolution_converged':ok})
    conv=[r for r in rows if r['resolution_converged']]
    r={'format':'SST-INTRINSIC-MODAL-RESOLUTION-2.1','candidate_counts':[len(c) for c in cs],'common_candidate_carrier_channels':len(common),'converged_candidate_carrier_channels':len(conv),'candidates':rows,'verdict':'PASS_RESOLUTION_PERSISTENT_STAGE_A_RECURRENCE' if conv else 'FAIL_OR_INDETERMINATE_NO_PERSISTENT_STAGE_A_RECURRENCE'}
    Path(out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8'); return r
