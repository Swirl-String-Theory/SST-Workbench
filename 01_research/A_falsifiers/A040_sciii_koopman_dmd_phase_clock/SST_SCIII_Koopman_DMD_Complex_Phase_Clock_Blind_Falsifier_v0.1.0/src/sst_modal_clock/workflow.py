from pathlib import Path
import json
import numpy as np
from .blind import prepare,prepare_provenance,scan_provenance,load_catalog
from .simulate import simulate_stage_a,simulate_stage_b
from .analyze import analyze_stage_a,analyze_stage_a_gauge,analyze_stage_b,analyze_provenance
from .sc2 import analyze_sc2_stage_a, analyze_sc2_gauge, analyze_sc2_provenance, analyze_sc2_stage_b
from .sciib import analyze_sciib_stage_a, analyze_sciib_gauge, analyze_sciib_provenance, analyze_sciib_stage_b
from .sciii import analyze_sciii_stage_a, analyze_sciii_gauge, analyze_sciii_provenance, analyze_sciii_stage_b
from .solver import backend_name
from .constants import GAMMA_CANON
from .util import clean_json
from .progress import BranchProgress
from .simulate import integration_plan

def cfg(path): return json.loads(Path(path).read_text())
def run_prepare(dataset,work,config): return prepare(dataset,work,cfg(config))
def run_prepare_provenance(work,config,libraries=None,min_carriers=None,kind=None,topology=None): return prepare_provenance(work,cfg(config),config_base=Path.cwd(),libraries=libraries,min_carriers=min_carriers,kind=kind,topology=topology)
def run_scan_provenance(config,libraries=None,min_carriers=None,kind=None,topology=None): return scan_provenance(cfg(config),config_base=Path.cwd(),libraries=libraries,min_carriers=min_carriers,kind=kind,topology=topology)

def _candidate_carriers(work,provisional=False):
    # Dedicated SC-IIb package: prefer pair/subspace manifests, then SC-II/SC-I
    # compatibility names. Branch physics is unchanged; only carrier selection differs.
    sciii='sciii_candidates_provisional.json' if provisional else 'sciii_candidates.json'
    sciib='sciib_candidates_provisional.json' if provisional else 'sciib_candidates.json'
    sc2='sc2_candidates_provisional.json' if provisional else 'sc2_candidates.json'
    legacy='stage_a_candidates_provisional.json' if provisional else 'stage_a_candidates.json'
    for name in (sciii,sciib,sc2,legacy):
        p=Path(work)/'analysis'/name
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8'));return {r['carrier_id'] for r in data.get('candidates',[])}
    return set()

def _branch_spec(branch,c):
    if branch=='stage_a': return 'stage_a',None,None,None
    if branch in ('stage_a_gauge_low','stage_a_gauge_high'):
        factor=float(c.get('mesh_gauge_low_factor',.7) if branch.endswith('low') else c.get('mesh_gauge_high_factor',1.3));return branch,_candidate_carriers,float(c.get('mesh_redistribution_rate',4.0))*factor,float(c.get('mesh_max_relative_rms',2.0))*factor
    return branch,_candidate_carriers,None,None

def run_branch(work,config,branch,limit=None):
    # BranchProgress emits carrier=... with print(..., flush=True) while preserving blind source identity.
    work=Path(work);c=cfg(config);rows=load_catalog(work);selected=None;outbranch,selector,mesh_override,cap_override=_branch_spec(branch,c)
    if branch in ('stage_a_gauge_low','stage_a_gauge_high'): selected=_candidate_carriers(work,provisional=True)
    elif branch in ('material','fixed'): selected=_candidate_carriers(work,provisional=False)
    od=work/f'results_{outbranch}/candidates';od.mkdir(parents=True,exist_ok=True);errs=[];done=0;skipped_existing=0;skipped_unselected=0;todo=[]
    for r in rows[:limit or None]:
        if selected is not None and r['carrier_id'] not in selected: skipped_unselected+=1;continue
        todo.append(r)
    total=len(todo);progress=BranchProgress(branch,total,work/'progress.log')
    for idx,r in enumerate(todo,1):
        out=od/f'{r["candidate_id"]}.npz'
        if out.exists(): skipped_existing+=1;progress.skip_candidate(idx,r['candidate_id']);continue
        candidate_start=None
        try:
            z=np.load(work/r['data'],allow_pickle=False);offsets=np.asarray(z['component_offsets'],dtype=np.int64) if 'component_offsets' in z.files else np.asarray([0,len(z['x'])],dtype=np.int64)
            if branch.startswith('stage_a'): plan=integration_plan(z['x_reference'],c,'stage_a_t_final',offsets)
            else:
                cc=dict(c);cc['t_final']=float(c.get('stage_b_t_final',4.0));plan=integration_plan(z['x_reference'],cc,'t_final',offsets)
            candidate_start=progress.start_candidate(idx,r['candidate_id'],r['carrier_id'],r['probe_arm'],r.get('n_components',1),plan['steps'],out.name)
            cb=lambda ev,idx=idx,r=r,cs=candidate_start: progress.heartbeat(idx,r['candidate_id'],cs,ev['step'],ev['planned_steps'],ev['sim_t'],ev['target_t_final'])
            if branch.startswith('stage_a'): info=simulate_stage_a(z['x'],z['x_reference'],c,out,mesh_rate_override=mesh_override,mesh_cap_override=cap_override,component_offsets=offsets,progress_callback=cb)
            else: info=simulate_stage_b(z['x'],z['x_reference'],z['reference_lengths'],c,out,branch,component_offsets=offsets,progress_callback=cb)
            done+=1;details=f't={info.get("actual_t_final",0):.6g}/{info.get("target_t_final",0):.6g} ds_cv={info.get("max_ds_cv",0):.5f} stop={info.get("stop_reason")}' +(f' mesh/phys={info.get("max_mesh_to_physical_rms_ratio",0):.3f}' if branch.startswith('stage_a') else '')
            progress.done_candidate(idx,r['candidate_id'],candidate_start,plan['steps'],details)
        except Exception as e:
            errs.append({'candidate_id':r['candidate_id'],'error':repr(e)});progress.error_candidate(idx,r['candidate_id'],candidate_start or progress.start_monotonic,repr(e))
    progress.finish(done,len(errs),skipped_existing)
    s={'format':'SST-INTRINSIC-MODAL-RUN-2.2.6','branch':branch,'backend':backend_name(),'n_run':done,'n_errors':len(errs),'n_skipped_existing':skipped_existing,'n_skipped_unselected':skipped_unselected,'selected_carriers':len(selected) if selected is not None else None,'mesh_rate_override':mesh_override,'mesh_cap_override':cap_override,'errors':errs,'gamma_canon_m2_s':GAMMA_CANON}
    (work/f'run_{branch}_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8');return s

def run_analyze_stage_a(work,config): return analyze_stage_a(work,cfg(config))
def run_analyze_stage_a_gauge(work,config): return analyze_stage_a_gauge(work,cfg(config))
def run_analyze_provenance(work,config): return analyze_provenance(work,cfg(config))
def run_analyze_stage_b(work,config): return analyze_stage_b(work,cfg(config))
def run_analyze_sc2_stage_a(work,config): return analyze_sc2_stage_a(work,cfg(config))
def run_analyze_sc2_gauge(work,config): return analyze_sc2_gauge(work,cfg(config))
def run_analyze_sc2_provenance(work,config): return analyze_sc2_provenance(work,cfg(config))
def run_analyze_sc2_stage_b(work,config): return analyze_sc2_stage_b(work,cfg(config))
def run_analyze_sciib_stage_a(work,config): return analyze_sciib_stage_a(work,cfg(config))
def run_analyze_sciib_gauge(work,config): return analyze_sciib_gauge(work,cfg(config))
def run_analyze_sciib_provenance(work,config): return analyze_sciib_provenance(work,cfg(config))
def run_analyze_sciib_stage_b(work,config): return analyze_sciib_stage_b(work,cfg(config))
def run_analyze_sciii_stage_a(work,config): return analyze_sciii_stage_a(work,cfg(config))
def run_analyze_sciii_gauge(work,config): return analyze_sciii_gauge(work,cfg(config))
def run_analyze_sciii_provenance(work,config): return analyze_sciii_provenance(work,cfg(config))
def run_analyze_sciii_stage_b(work,config): return analyze_sciii_stage_b(work,cfg(config))
def reveal(work):
    work=Path(work);priv=json.loads((work/'private/reveal_map.json').read_text())
    blind=json.loads((work/'analysis/blind_sciii_summary.json').read_text()) if (work/'analysis/blind_sciii_summary.json').exists() else {}
    sa=json.loads((work/'analysis/blind_sciii_stage_a_summary.json').read_text()) if (work/'analysis/blind_sciii_stage_a_summary.json').exists() else {}
    sg=json.loads((work/'analysis/blind_sciii_gauge_summary.json').read_text()) if (work/'analysis/blind_sciii_gauge_summary.json').exists() else {}
    sp=json.loads((work/'analysis/blind_sciii_provenance_summary.json').read_text()) if (work/'analysis/blind_sciii_provenance_summary.json').exists() else {}
    out={'format':'SST-SCIII-REVEAL-1.0','blind_primary_gate':blind.get('primary_gate'),'blind_stage_a_gate':sa.get('primary_gate'),'blind_stage_a_gauge_gate':sg.get('primary_gate'),'blind_provenance_gate':sp.get('primary_gate'),'secret_probe_flip':priv['secret_probe_flip'],'mapping':priv['rows']}
    (work/'analysis/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return out
