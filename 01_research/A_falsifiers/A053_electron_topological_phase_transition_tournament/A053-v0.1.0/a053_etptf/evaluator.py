from __future__ import annotations
import json, math, hashlib
from collections import defaultdict
from pathlib import Path
from .metrics import circular_order, rel_residual, closest_link_class, window_indices, subset, fraction, mean

PASS='PASS'; FAIL='FAIL'; INDET='INDETERMINATE'; NA='NOT_APPLICABLE'

class EvaluationError(RuntimeError): pass

def _gate(ok, detail='', indeterminate=False):
    return {'status': INDET if indeterminate else (PASS if ok else FAIL), 'detail': detail}

def _validate_case(c):
    req=['case_id','hypothesis','resolution','circulation_sector','sham','time','component_count','abs_linking','energy','helicity','interaction_mask','reconnection_events']
    miss=[k for k in req if k not in c]
    if miss: raise EvaluationError(f"case {c.get('case_id','?')} missing {miss}")
    n=len(c['time'])
    for k in ['component_count','abs_linking','energy','helicity','interaction_mask']:
        if len(c[k])!=n: raise EvaluationError(f"case {c['case_id']} length mismatch: {k}")
    if c['hypothesis'] not in {'H0','H1','H2','H3'}: raise EvaluationError('bad hypothesis')

def evaluate_case(case, cfg, producer):
    _validate_case(case)
    h=case['hypothesis']; t=case['time']; comp=case['component_count']; lk=case['abs_linking']
    pre,pulse,post=window_indices(t,cfg)
    tol=cfg['topology']['link_tolerance']; persist=cfg['topology']['post_persistence_fraction']
    gates={}
    gates['G03_INITIAL_TOPOLOGY']=_gate(
        (h in {'H0','H3'} and pre and fraction(comp[i]==1 for i in pre)>=0.95) or
        (h in {'H1','H2'} and pre and fraction(comp[i]==2 and closest_link_class(lk[i],tol)=='L2a1_like' for i in pre)>=0.95),
        'initial topology matches preregistration')
    # free propagation = pre window; survival repeats initial requirement deliberately as its own audit gate
    gates['G04_FREE_PROPAGATION_SURVIVAL']=gates['G03_INITIAL_TOPOLOGY'].copy()
    er=rel_residual(case['energy']); hr=rel_residual(case['helicity'])
    gates['G08_ENERGY_ACCOUNTING']=_gate(math.isfinite(er) and er<=cfg['accounting']['relative_energy_residual_max'], f'rel_residual={er:.6g}' if math.isfinite(er) else 'missing')
    gates['G09_HELICITY_ACCOUNTING']=_gate(math.isfinite(hr) and hr<=cfg['accounting']['relative_helicity_residual_max'], f'rel_residual={hr:.6g}' if math.isfinite(hr) else 'missing')
    gates['G10_TARGET_BLIND_RECONNECTION']=_gate(not bool(producer.get('target_aware_reconnection',True)), 'producer must declare target_aware_reconnection=false')
    topo_change_allowed=producer.get('physics_class') in {'finite_core_reconnection','reconnection_capable'}
    if h=='H0':
        gates['H0_TOPOLOGY_PERSISTS']=_gate(post and fraction(comp[i]==1 for i in post)>=persist,'post window remains one-component')
        gates['H0_NO_UNDECLARED_RECONNECTION']=_gate(len(case['reconnection_events'])==0,'no reconnection event')
    elif h=='H1':
        gates['H1_L2A1_PERSISTS']=_gate(post and fraction(comp[i]==2 and closest_link_class(lk[i],tol)=='L2a1_like' for i in post)>=persist,'post window remains Hopf-like')
        phase=case.get('phase12'); weight=case.get('phase_weight')
        present=phase is not None and len(phase)==len(t)
        gates['H1_PHASE_OBSERVABLE_PRESENT']=_gate(present,'independent phase12 time series required',indeterminate=not present)
        if present:
            w=weight if weight is not None else [1.0]*len(t)
            rpre=circular_order(subset(phase,pre),subset(w,pre)); rpost=circular_order(subset(phase,post),subset(w,post))
            gates['H1_LOCK_GAIN']=_gate(math.isfinite(rpre) and math.isfinite(rpost) and (rpost-rpre)>=cfg['phase']['lock_gain_min'] and rpost>=cfg['phase']['post_lock_min'],f'Rpre={rpre:.6g}, Rpost={rpost:.6g}')
            gates['H1_POST_LOCK_PERSISTS']=_gate(math.isfinite(rpost) and rpost>=cfg['phase']['post_lock_min'],f'Rpost={rpost:.6g}')
        else:
            gates['H1_LOCK_GAIN']=_gate(False,'missing phase',indeterminate=True); gates['H1_POST_LOCK_PERSISTS']=_gate(False,'missing phase',indeterminate=True)
    elif h=='H2':
        gates['H2_MODEL_CLASS_ALLOWS_TOPOLOGY_CHANGE']=_gate(topo_change_allowed,producer.get('physics_class','missing'),indeterminate=not topo_change_allowed)
        gates['H2_LINKING_1_TO_2']=_gate(post and fraction(comp[i]==2 and closest_link_class(lk[i],tol)=='L4a1_like' for i in post)>=persist,'post |Lk| approximately 2')
        during=any(pre and cfg['windows']['pre_end'] < float(e.get('time',-1)) <= cfg['windows']['pulse_end'] for e in case['reconnection_events'])
        gates['H2_EVENT_DURING_INTERACTION']=_gate(during,'reconnection event must lie in pulse window')
        gates['H2_POST_L4A1_PERSISTS']=gates['H2_LINKING_1_TO_2'].copy()
    elif h=='H3':
        gates['H3_MODEL_CLASS_ALLOWS_TOPOLOGY_CHANGE']=_gate(topo_change_allowed,producer.get('physics_class','missing'),indeterminate=not topo_change_allowed)
        middle=[i for i,tv in enumerate(t) if cfg['windows']['pre_end'] < float(tv) < cfg['windows']['post_start']]
        frac_multi=fraction(comp[i]>=2 for i in middle)
        frac_link=fraction(comp[i]>=2 and closest_link_class(lk[i],tol) in {'L2a1_like','L4a1_like'} for i in middle)
        gates['H3_TRANSIENT_MULTICOMPONENT']=_gate(frac_multi>=cfg['topology']['compound_fraction_min'],f'fraction={frac_multi:.6g}')
        gates['H3_COMPOUND_LINKING_SIGNATURE']=_gate(frac_link>=cfg['topology']['compound_fraction_min'],f'fraction={frac_link:.6g}')
        during=any(cfg['windows']['pre_end'] < float(e.get('time',-1)) <= cfg['windows']['pulse_end'] for e in case['reconnection_events'])
        gates['H3_EVENT_DURING_INTERACTION']=_gate(during,'event in pulse window')
        gates['H3_RETURN_TO_ONE_COMPONENT']=_gate(post and fraction(comp[i]==1 for i in post)>=persist,'returns to one component')
    return {'case_id':case['case_id'],'hypothesis':h,'sham':bool(case['sham']),'resolution':case['resolution'],'source_group':case.get('source_group','unknown'),'circulation_sector':case['circulation_sector'],'metrics':{'energy_residual':er,'helicity_residual':hr},'gates':gates}

def _case_pass(ev):
    sts=[g['status'] for g in ev['gates'].values()]
    if FAIL in sts: return FAIL
    if INDET in sts: return INDET
    return PASS

def evaluate_manifest(manifest, cfg):
    if manifest.get('schema')!='A053-PRODUCER-v1': raise EvaluationError('wrong schema')
    if manifest.get('blind') is not True: raise EvaluationError('physical evaluator requires blind=true manifest')
    producer=manifest.get('producer',{})
    case_evals=[evaluate_case(c,cfg,producer) for c in manifest.get('cases',[])]
    # sham controls: a hypothesis cannot count topology transition if its matching sham does same.
    by_key=defaultdict(list)
    for c,e in zip(manifest['cases'],case_evals):
        by_key[(c['hypothesis'],c['resolution'],c.get('source_group','unknown'),c['circulation_sector'])].append((c,e))
    for key,pairs in by_key.items():
        h=key[0]
        if h not in {'H2','H3'}: continue
        shams=[(c,e) for c,e in pairs if c['sham']]
        acts=[(c,e) for c,e in pairs if not c['sham']]
        sham_transition=False
        for c,e in shams:
            if h=='H2': sham_transition |= e['gates'].get('H2_LINKING_1_TO_2',{}).get('status')==PASS
            else: sham_transition |= e['gates'].get('H3_TRANSIENT_MULTICOMPONENT',{}).get('status')==PASS
        for c,e in acts:
            nm='H2_SHAM_DOES_NOT_TRANSITION' if h=='H2' else 'H3_SHAM_DOES_NOT_COMPOUND'
            e['gates'][nm]=_gate(bool(shams) and not sham_transition,'matched sham present and negative' if shams else 'no matched sham',indeterminate=not bool(shams))
    # Aggregate without scalar override.
    hypotheses={}
    for h in ['H0','H1','H2','H3']:
        actual=[e for e in case_evals if e['hypothesis']==h and not e['sham']]
        if not actual:
            hypotheses[h]={'status':INDET,'detail':'no physical cases','case_statuses':[]}; continue
        cs=[_case_pass(e) for e in actual]
        if FAIL in cs: st=FAIL
        elif INDET in cs: st=INDET
        else: st=PASS
        # resolution/source robustness prerequisites
        res=len({e['resolution'] for e in actual}); src=len({e['source_group'] for e in actual})
        robust=(res>=cfg['numerics']['min_resolutions'] and src>=cfg['numerics']['min_source_groups'])
        if st==PASS and not robust: st=INDET
        hypotheses[h]={'status':st,'detail':f'cases={len(actual)}, resolutions={res}, source_groups={src}','case_statuses':cs}
    survivors=[h for h,v in hypotheses.items() if v['status']==PASS]
    if len(survivors)==0: verdict='NO_SURVIVOR_TESTED_DOMAIN'
    elif len(survivors)==1: verdict='UNIQUE_SURVIVOR_TESTED_DOMAIN'
    else: verdict='NON_UNIQUE_SURVIVORS_TESTED_DOMAIN'
    raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()
    return {'schema':'A053-TOURNAMENT-v1','blind':True,'input_sha256':hashlib.sha256(raw).hexdigest(),'producer':producer,'hypotheses':hypotheses,'survivors':survivors,'verdict':verdict,'cases':case_evals}
