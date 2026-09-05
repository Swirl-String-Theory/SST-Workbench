from pathlib import Path
import json,numpy as np


def _candidates(work):
    work=Path(work); p=work/'analysis/sciib_candidates.json'; sciib=p.exists()
    if not p.exists(): p=work/'analysis/stage_a_candidates.json'
    if not p.exists(): return {},sciib
    data=json.loads(p.read_text(encoding='utf-8')); out={}
    for r in data.get('candidates',[]):
        key=(r['carrier_id'],r.get('channel','natural'))
        score=float(r.get('combined_energy_fraction') if sciib else r.get('discovery_energy_fraction') or 0)
        if key not in out or score>out[key][0]:
            if sciib:
                met={'period':float(r.get('period',np.nan)),'omega':float(r.get('omega',np.nan)),'phase_diffusion':float(r.get('phase_diffusion_rms_rad',np.nan)),'mode_i':int(r.get('mode_i',0)),'mode_j':int(r.get('mode_j',1))}
            else:
                met={'period':float(r.get('period',np.nan)),'closure':float(r.get('closure_median',np.nan)),'period_cv':float(r.get('period_cv',np.nan)),'mode_index':int(r.get('mode_index',0))}
            out[key]=(score,met)
    return {k:v[1] for k,v in out.items()},sciib


def compare(works,out):
    loaded=[_candidates(w) for w in works]; cs=[x[0] for x in loaded]; sciib=bool(loaded and all(x[1] for x in loaded)); common=set(cs[0]) if cs else set()
    for c in cs[1:]: common &= set(c)
    rows=[]
    def spread(a):
        a=np.asarray(a,float); a=a[np.isfinite(a)]; return float((a.max()-a.min())/max(abs(np.median(a)),1e-15)) if len(a)==3 else float('inf')
    for key in sorted(common):
        periods=[c[key]['period'] for c in cs]; ps=spread(periods)
        if sciib:
            omegas=[c[key]['omega'] for c in cs]; diffs=[c[key]['phase_diffusion'] for c in cs]; os=spread(omegas); ds=spread(diffs); ok=ps<=.20 and os<=.20 and ds<=.50
            rows.append({'carrier_id':key[0],'channel':key[1],'periods':periods,'omegas':omegas,'phase_diffusions':diffs,'relative_period_spread':ps,'relative_omega_spread':os,'relative_phase_diffusion_spread':ds,'resolution_converged':ok})
        else:
            closures=[c[key]['closure'] for c in cs]; cspr=spread(closures); ok=ps<=.20 and cspr<=.35
            rows.append({'carrier_id':key[0],'channel':key[1],'periods':periods,'closures':closures,'relative_period_spread':ps,'relative_closure_spread':cspr,'resolution_converged':ok})
    conv=[r for r in rows if r['resolution_converged']]
    if sciib:
        verdict='PASS_RESOLUTION_PERSISTENT_SCIIB_PAIR_PHASE_CLOCK' if conv else 'FAIL_OR_INDETERMINATE_NO_RESOLUTION_PERSISTENT_SCIIB_PAIR_PHASE_CLOCK'; fmt='SST-SCIIB-RESOLUTION-1.0'
    else:
        verdict='PASS_RESOLUTION_PERSISTENT_STAGE_A_RECURRENCE' if conv else 'FAIL_OR_INDETERMINATE_NO_PERSISTENT_STAGE_A_RECURRENCE'; fmt='SST-INTRINSIC-MODAL-RESOLUTION-2.2'
    r={'format':fmt,'candidate_counts':[len(c) for c in cs],'common_candidate_carrier_channels':len(common),'converged_candidate_carrier_channels':len(conv),'candidates':rows,'verdict':verdict}
    Path(out).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n',encoding='utf-8'); return r
