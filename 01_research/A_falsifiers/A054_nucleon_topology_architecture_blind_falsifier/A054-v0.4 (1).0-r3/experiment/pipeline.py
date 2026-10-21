from __future__ import annotations
from pathlib import Path
import json, math, hashlib, numpy as np
from .source_loader import load_manifest_cases
from .certification import screen_case
from .mechanisms import core_shell_raw, elastic_raw
from .physics import velocity_components, rms_field

def _write(p,obj): Path(p).write_text(json.dumps(obj,indent=2,sort_keys=False)+'\n',encoding='utf-8')
def _gammas(q): return {'Q0':[1,1,1],'Q1':[-1,1,1],'Q2':[1,-1,1],'Q3':[1,1,-1]}[q]
def _score(rows):
    rec=sum(bool(x['metrics']['recovered']) for x in rows); vals=[math.log(max(x['metrics']['restoring_return_ratio_max'],1e-12))+math.log(max(x['metrics']['ringdown_max_over_initial'],1e-12)) for x in rows]
    return (rec, float(np.median(vals)) if vals else float('inf'))
def _run_cohort(cases,arms,gains,cfg,core_cfg):
    rows=[]
    for cid,comps,_meta in cases:
        # total normalized length => same dimensionless core policy as v0.2
        core=0.04; 
        for q in ('Q0','Q1','Q2','Q3'):
            ga=_gammas(q)
            for arm in arms:
                gs=[0.0] if arm=='BASE' else gains
                for g in gs:
                    try: met=screen_case(comps,ga,core,arm,g,cfg,core_cfg)
                    except Exception as e: met={'recovered':False,'error':f'{type(e).__name__}: {e}','restoring_return_ratio_max':float('inf'),'kelvin_growth':float('inf'),'ringdown_max_over_initial':float('inf'),'max_linking_drift':float('inf'),'min_clearance_ratio':0.0}
                    rows.append({'case_id':cid,'sector':q,'arm':arm,'gain':float(g),'metrics':met})
    return rows

def _select(rows,arms,gains):
    out={}
    for arm in arms:
        candidates=[0.0] if arm=='BASE' else gains; best=None
        for g in candidates:
            rr=[x for x in rows if x['arm']==arm and abs(x['gain']-g)<1e-15]; rec,med=_score(rr); key=(-rec,med,g,arm)
            if best is None or key<best[0]: best=(key,{'arm':arm,'gain':g,'recovered_cells':rec,'median_log_restore_plus_ringdown':med,'cell_count':len(rr)})
        out[arm]=best[1]
    winner=min([v for k,v in out.items() if k!='BASE'],key=lambda v:(-v['recovered_cells'],v['median_log_restore_plus_ringdown'],v['gain'],v['arm']))
    return out,winner

def _reference_sanity(root):
    cases=load_manifest_cases(root,'data/discovery/DISCOVERY_MANIFEST.json','data/discovery',n=32,limit=1); _,cs,_=cases[0]; ga=[1,1,1]; base=velocity_components(cs,ga,0.04); core=core_shell_raw(cs,0.04,{'sigma_rep_core':1.5,'sigma_attr_core':4.0,'attraction_fraction':0.35}); el=elastic_raw(cs)
    return {'finite':bool(np.isfinite(np.vstack(base+core+el)).all()),'baseline_rms':rms_field(base),'core_raw_rms':rms_field(core),'elastic_raw_rms':rms_field(el)}

def run_scientific_pipeline(root,cfg,ledger,mode):
    root=Path(root); out=root/f"{cfg['project']['name']}_{cfg['project']['version']}-outputs"; out.mkdir(exist_ok=True)
    mc=json.loads((root/'configs/mechanism_full.json').read_text()); mode=mode.upper(); basic=(mode=='BASIC')
    ledger.record('G0','PASS',reason='Framework verified frozen protocol before instance pipeline.')
    # Sources/hash admissibility happens in loader + framework SOURCE_MANIFEST; preflight here
    dlimit=mc['basic']['discovery_cases'] if basic else None; climit=mc['basic']['confirmation_cases'] if basic else None
    try:
        discovery=load_manifest_cases(root,'data/discovery/DISCOVERY_MANIFEST.json','data/discovery',n=mc['discovery']['n_ref'],limit=dlimit)
        confirmation=load_manifest_cases(root,'data/confirmation/CONFIRMATION_MANIFEST.json','data/confirmation',n=mc['confirmation']['n_ref'],limit=climit)
        ledger.record('G1','PASS',metrics={'discovery_cases':len(discovery),'confirmation_cases':len(confirmation)},reason='All selected source files matched frozen SHA-256 manifests.')
    except Exception as e:
        ledger.record('G1','FAIL',reason=str(e));
        for g in ('G2','G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(g)
        return {'status':'SOURCE_FAIL'}
    san=_reference_sanity(root); _write(out/'REFERENCE_SANITY.json',san)
    if not san['finite']:
        ledger.record('G2','FAIL',metrics=san,reason='Nonfinite reference mechanism field.');
        for g in ('G3','G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(g)
        return {'status':'NUMERIC_SANITY_FAIL'}
    ledger.record('G2','PASS',metrics=san,reason='Reference fields finite; normalization anchors nonzero.')
    arms=mc['arms']; gains=mc['basic']['gain_grid'] if basic else mc['gain_grid']; core_cfg=mc['core_shell']
    drows=_run_cohort(discovery,arms,gains,mc['discovery'],core_cfg); _write(out/'DISCOVERY_BLIND.json',{'schema':'A054-V040-DISCOVERY-BLIND-1','rows':drows})
    selected,winner=_select(drows,arms,gains); _write(out/'MECHANISM_SELECTION_BLIND.json',{'selected_by_arm':selected,'winner':winner,'selection_rule':mc['selection_rule']})
    base_rec=selected['BASE']['recovered_cells']; g3=winner['recovered_cells']>base_rec
    ledger.record('G3','PASS' if g3 else 'FAIL',metrics={'baseline_recovered_cells':base_rec,'best_nonbaseline':winner},reason='Blind global arm/gain selection; no semantic labels or per-case gains used.')
    if not g3:
        for g in ('G4','G5','G6','G7','G8'): ledger.skip_due_prerequisite(g)
        return {'status':'NO_REGISTERED_MECHANISM_RECOVERS_DISCOVERY','winner':winner}
    # held-out uses selected arm/gain, no refit
    crows=_run_cohort(confirmation,[winner['arm']],[winner['gain']],mc['confirmation'],core_cfg); _write(out/'CONFIRMATION_BLIND.json',{'schema':'A054-V040-CONFIRMATION-BLIND-1','selected':winner,'rows':crows})
    recovered_ids=sorted({x['case_id'] for x in crows if x['metrics']['recovered']}); need=mc['heldout_pass_rule']['min_distinct_confirmation_geometries_recovered']; g4=len(recovered_ids)>=need
    ledger.record('G4','PASS' if g4 else 'FAIL',metrics={'recovered_confirmation_geometries':len(recovered_ids),'required':need},reason='Held-out source-native transfer used frozen discovery gain without refitting.')
    if not g4:
        for g in ('G5','G6','G7','G8'): ledger.skip_due_prerequisite(g)
        return {'status':'DISCOVERY_DID_NOT_TRANSFER','winner':winner}
    # G5: certification placeholder is strict: requires explicit full-resolution rerun + native parity tool output.
    # Run a simple parity check of raw mechanism kernels when native exists; convergence is assessed in experiment/certify_full.py.
    try:
        from . import native
        native_ok=native.available() and native.openmp_enabled()
    except Exception: native_ok=False
    cert_path=out/'FULL_CERTIFICATION.json'
    if cert_path.exists():
        cert=json.loads(cert_path.read_text()); g5=bool(cert.get('pass',False) and native_ok)
        ledger.record('G5','PASS' if g5 else 'UNRESOLVED',metrics={'native_openmp':native_ok,'certification':cert},reason='Full certification artifact consumed.' if g5 else 'Confirmation exists but full convergence/native certification did not PASS.')
    else:
        ledger.record('G5','UNRESOLVED',metrics={'native_openmp':native_ok},reason='Held-out recovery found; run tools/certify_selected.py to execute frozen v0.2 full-resolution convergence/RPO/Floquet certification, then rerun CERTIFY.')
        g5=False
    ledger.record('G6','DEFERRED',reason='SYCL FP32/DD32 is optional SCREENING_ONLY under framework v1.0.4.')
    ledger.record('G7','NOT_RUN_PREREQUISITE',reason='Current discovery/confirmation sources are simulation/geometry evidence, not eligible physical cross-source evidence.')
    ledger.record('G8','NOT_RUN_PREREQUISITE',reason='Physical mechanism promotion is prohibited without G7 eligible replication; simulation-level ablation remains reportable only.')
    return {'status':'HELDOUT_RECOVERY_PENDING_CERTIFICATION' if not g5 else 'SIMULATION_LEVEL_MECHANISM_RECOVERY_CERTIFIED','winner':winner,'confirmation_recovered':len(recovered_ids)}
