from __future__ import annotations
import json,hashlib,platform,sys,os
from pathlib import Path
import numpy as np
from .filament import evolve_curve
from .persistence import modal_persistence_metrics
from .nonstationary import branch_retained
from .mechanisms import mechanism_metrics
from .io import write_json,write_csv,sha256
ROOT=Path(__file__).resolve().parents[1]
MECHANISMS=('smooth_chirp','two_tone_beating','phase_slip','rpo_candidate','amplitude_phase_modulation')

def clean(x):
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list): return [clean(v) for v in x]
    if isinstance(x,(np.bool_,bool)): return bool(x)
    if isinstance(x,(np.integer,int)): return int(x)
    if isinstance(x,(np.floating,float)): return None if not np.isfinite(x) else float(x)
    return x

def env(): return {'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'cpu_count':os.cpu_count()}
def load_manifest(cfg): return json.loads((ROOT/cfg['mechanism_gate']['fresh_staged_manifest']).read_text(encoding='utf-8'))
def load_entry(e):
    p=ROOT/e['file']; h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=e['sha256']: raise RuntimeError(f'staged hash mismatch: {e["carrier_id"]}')
    return np.asarray(np.load(p,allow_pickle=False)['points'],float)
def run_carrier(points,cfg):
    dt=float(cfg['time_step']); frames=evolve_curve(points,float(cfg['core_ratio']),dt,int(cfg['modal_persistence_steps']),int(cfg['reparameterize_every']),int(cfg['field_chunk']))
    pm=modal_persistence_metrics(frames,dt,cfg['modal_persistence_gate'],cfg['kelvin_gate']); bp,mech=mechanism_metrics(frames,dt,pm,cfg['kelvin_gate'],cfg['branch_phase_gate'],cfg['mechanism_gate']); return pm,bp,mech
def flags(rec): return (rec.get('mechanism') or {}).get('flags',{})

def main_run(config_path,out_dir):
    cfg=json.loads(Path(config_path).read_text(encoding='utf-8')); gate=cfg['mechanism_gate']; man=load_manifest(cfg); parent=json.loads((ROOT/gate['parent_v032_evidence']).read_text(encoding='utf-8'))
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True); write_json(out/'config_used.json',cfg); write_json(out/'environment.json',env()); write_json(out/'staged_manifest_used.json',man); write_json(out/'parent_v032_evidence_used.json',parent)
    groups={}
    for e in man['entries']: groups.setdefault(e['group_id'],[]).append(e)
    primary=[]; diagnostics=[]; flat=[]
    for gid,ents in sorted(groups.items()):
        be=next(e for e in ents if e['role']=='baseline'); pm,bp,mm=run_carrier(load_entry(be),cfg); base={'carrier_id':be['carrier_id'],'group_id':gid,'role':'baseline','persistence':pm,'branch_phase':bp,'mechanism':mm}; flat.append(base)
        holds=[]
        for e in sorted([x for x in ents if x['role']=='holdout'],key=lambda x:x['carrier_id']):
            hp,hb,hm=run_carrier(load_entry(e),cfg); rec={'carrier_id':e['carrier_id'],'group_id':gid,'role':'holdout','persistence':hp,'branch_phase':hb,'mechanism':hm,'perturbation_rms':e.get('perturbation_rms')}; holds.append(rec); flat.append(rec)
        if not be.get('primary',False): diagnostics.append({'group_id':gid,'baseline':base}); print(f'[v0.4.0] {gid} diagnostic mechanism={mm["label"]}',flush=True); continue
        retained=[h for h in holds if branch_retained(bp['branch_identity'],h['branch_phase']['branch_identity'])]; replication={}; bflags=flags(base)
        for m in MECHANISMS:
            support=[h for h in retained if flags(h).get(m,False)]; frac=float(len(support)/max(len(holds),1))
            replicated=bool(bflags.get(m,False) and frac>=float(gate['minimum_fresh_holdout_mechanism_fraction_per_base']))
            replication[m]={'baseline_support':bool(bflags.get(m,False)),'branch_retained_holdout_support_count':len(support),'holdout_count':len(holds),'holdout_support_fraction_of_all':frac,'replicated':replicated}
        primary.append({'group_id':gid,'source_group_id':be['source_group_id'],'baseline':base,'holdouts':holds,'fresh_branch_retained_holdout_count':len(retained),'fresh_holdout_count':len(holds),'fresh_branch_retention_fraction':float(len(retained)/max(len(holds),1)),'mechanism_replication':replication})
        print(f'[v0.4.0] {gid} branch={bp["selected_mode"]} retained={len(retained)}/{len(holds)} mechanism={mm["label"]}',flush=True)
    summaries=[]
    for m in MECHANISMS:
        replicated=[r for r in primary if r['mechanism_replication'][m]['replicated']]; source=[]
        for sid,need in sorted(cfg['external_geometry_gate']['source_group_minimum_robust_bases'].items()):
            rr=[r for r in primary if r['source_group_id']==sid]; n=sum(r['mechanism_replication'][m]['replicated'] for r in rr); source.append({'source_group_id':sid,'replicated_base_count':int(n),'base_count':len(rr),'minimum_required':int(need),'pass':bool(n>=int(need))})
        source_ok=sum(s['pass'] for s in source)>=int(cfg['external_geometry_gate']['minimum_source_groups_confirmed']); passed=bool(len(replicated)>=int(gate['minimum_replicated_primary_bases_per_mechanism']) and source_ok)
        summaries.append({'mechanism':m,'pass':passed,'replicated_primary_base_count':len(replicated),'primary_base_count':len(primary),'minimum_replicated_primary_bases':int(gate['minimum_replicated_primary_bases_per_mechanism']),'source_group_rows':source,'source_groups_confirmed':sum(s['pass'] for s in source)})
    passed=[x['mechanism'] for x in summaries if x['pass']]; branch_rep=sum(r['fresh_branch_retention_fraction']>=float(gate['minimum_fresh_branch_retention_fraction_per_base']) for r in primary); branch_gate=bool(branch_rep>=int(gate['minimum_primary_bases_with_fresh_branch_retention']))
    if not branch_gate: status='FRESH_HOLDOUT_BRANCH_RETENTION_FAILED'
    elif len(passed)==1: status='MECHANISM_'+passed[0].upper()+'_FRESH_HOLDOUT_REPLICATED'
    elif len(passed)>1: status='MULTIPLE_MECHANISMS_FRESH_HOLDOUT_REPLICATED'
    else: status='COHERENT_NONSTATIONARITY_MECHANISM_UNRESOLVED'
    result={'stage':'blind_mechanism_discrimination_complete','blind':True,'version':'v0.4.0','parent_version':'v0.3.2','parent_diagnostic_status_frozen':parent['parent_diagnostic_status'],'parent_blind_results_sha256':parent['blind_results_sha256'],'mechanism_status':status,'passed_mechanisms':passed,'does_not_modify_parent_v030_or_v032_results':True,'fresh_holdout_replication':{'branch_gate_pass':branch_gate,'retained_primary_base_count':int(branch_rep),'primary_base_count':len(primary),'minimum_primary_bases':int(gate['minimum_primary_bases_with_fresh_branch_retention']),'fresh_holdout_seed':int(gate['fresh_holdout_seed']),'fresh_holdouts_per_base':int(gate['fresh_holdout_replicates_per_primary_base'])},'mechanism_summary':summaries,'primary_groups':primary,'diagnostic_groups':diagnostics,'hypotheses':{'smooth_chirp':'A smoothly accelerating/decelerating branch phase should be described by a coherent quadratic phase law with no sign reversal.','two_tone_beating':'Two coherent complex-frequency components should outperform a one-tone model; their beat rate should match envelope modulation; reversal/amplitude coincidence is an additional diagnostic.','phase_slip':'Apparent reversals should be explained by abrupt phase increments concentrated at low-amplitude events.','rpo_candidate':'After quotienting the spatial phase action C_m -> C_m exp(-i*m*theta), the modal state should repeatedly near-return at a nontrivial lag with concentrated group-phase advance.','amplitude_phase_modulation':'Angular-rate variation should couple reproducibly to the selected-mode amplitude envelope after simple beating/slip signatures are excluded.'},'limitations':['Mechanism hypotheses were chosen after v0.3.2 and are post-hoc with respect to the five baseline trajectories.','Fresh v0.4.0 holdouts are prospective perturbation replicates but are not a new upstream geometry provider.','RPO_CANDIDATE is only a recurrence gate; no Floquet or monodromy claim is permitted in v0.4.0.','A numerical mechanism signature in this dimensionless filament model is not by itself an SST validation or physical Kelvin-wave identification.']}
    result=clean(result); write_json(out/'blind_results.json',result)
    rows=[]
    for r in flat:
        bp=r['branch_phase']; ph=bp.get('phase',{}); mm=r['mechanism']; tone=mm.get('two_tone',{}); inst=mm.get('instantaneous_rate',{}); slip=mm.get('phase_slip',{}); rec=mm.get('recurrence',{}); best=rec.get('best') or {}; chirp=mm.get('smooth_chirp',{})
        rows.append({'carrier_id':r['carrier_id'],'group_id':r['group_id'],'role':r['role'],'branch_mode':bp.get('selected_mode'),'branch_stable':bp.get('branch_identity',{}).get('stable'),'phase_class':ph.get('classification'),'mechanism_label':mm.get('label'),'smooth_chirp':flags(r).get('smooth_chirp'),'chirp_quadratic_r2':chirp.get('quadratic_r2'),'two_tone_beating':flags(r).get('two_tone_beating'),'two_tone_delta_bic':tone.get('delta_bic_two_over_one'),'two_tone_nrmse':(tone.get('two_tone') or {}).get('nrmse'),'beat_cycles':tone.get('beat_cycles_over_horizon'),'reversal_count':inst.get('reversal_count'),'reversal_amplitude_dip_fraction':inst.get('reversal_amplitude_dip_fraction'),'amplitude_rate_max_abs_correlation':inst.get('amplitude_rate_max_abs_correlation'),'phase_slip':flags(r).get('phase_slip'),'phase_slip_event_count':slip.get('event_count'),'rpo_candidate':flags(r).get('rpo_candidate'),'quotient_recurrence':flags(r).get('quotient_recurrence'),'recurrence_lag_steps':best.get('lag_steps'),'recurrence_distance':best.get('median_quotient_distance'),'group_phase_advance_concentration':best.get('group_phase_advance_concentration'),'amplitude_phase_modulation':flags(r).get('amplitude_phase_modulation')})
    write_csv(out/'mechanism_carriers.csv',rows)
    write_csv(out/'mechanism_bases.csv',[{'group_id':r['group_id'],'source_group_id':r['source_group_id'],'baseline_mechanism_label':r['baseline']['mechanism']['label'],'fresh_branch_retention_fraction':r['fresh_branch_retention_fraction'],**{f'{m}_replicated':r['mechanism_replication'][m]['replicated'] for m in MECHANISMS},**{f'{m}_holdout_fraction':r['mechanism_replication'][m]['holdout_support_fraction_of_all'] for m in MECHANISMS}} for r in primary]); write_csv(out/'mechanism_summary.csv',summaries)
    dig=sha256(out/'blind_results.json'); (out/'blind_results.sha256').write_text(dig+'  blind_results.json\n',encoding='utf-8'); return result
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--config',required=True); ap.add_argument('--out',required=True); a=ap.parse_args(); main_run(a.config,a.out)
