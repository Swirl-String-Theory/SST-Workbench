from pathlib import Path
import json,sys
import numpy as np
from .blind import prepare,load_catalog
from .simulate import simulate_stage_a,simulate_stage_b
from .analyze import analyze_stage_a,analyze_stage_a_gauge,analyze_stage_b
from .solver import backend_name
from .constants import GAMMA_CANON
from .util import clean_json

def cfg(path): return json.loads(Path(path).read_text())
def run_prepare(dataset,work,config): return prepare(dataset,work,cfg(config))

def _candidate_carriers(work,provisional=False):
    name='stage_a_candidates_provisional.json' if provisional else 'stage_a_candidates.json'; p=Path(work)/'analysis'/name
    if not p.exists(): return set()
    data=json.loads(p.read_text(encoding='utf-8')); return {r['carrier_id'] for r in data.get('candidates',[])}

def _branch_spec(branch,c):
    if branch=='stage_a': return 'stage_a',None,None
    if branch=='stage_a_gauge_low': return branch,_candidate_carriers, float(c.get('mesh_redistribution_rate',4.0))*float(c.get('mesh_gauge_low_factor',.6))
    if branch=='stage_a_gauge_high': return branch,_candidate_carriers, float(c.get('mesh_redistribution_rate',4.0))*float(c.get('mesh_gauge_high_factor',1.4))
    return branch,_candidate_carriers,None

def run_branch(work,config,branch,limit=None):
    work=Path(work); c=cfg(config); rows=load_catalog(work); selected=None; outbranch,selector,mesh_override=_branch_spec(branch,c)
    if branch in ('stage_a_gauge_low','stage_a_gauge_high'): selected=_candidate_carriers(work,provisional=True)
    elif branch in ('material','fixed'): selected=_candidate_carriers(work,provisional=False)
    od=work/f'results_{outbranch}/candidates'; od.mkdir(parents=True,exist_ok=True); errs=[]; done=0; skipped_existing=0; skipped_unselected=0
    todo=[]
    for r in rows[:limit or None]:
        if selected is not None and r['carrier_id'] not in selected: skipped_unselected+=1; continue
        todo.append(r)
    total=len(todo)
    for idx,r in enumerate(todo,1):
        out=od/f'{r["candidate_id"]}.npz'
        if out.exists():
            skipped_existing+=1; print(f'[{branch} {idx:03d}/{total:03d}] skip existing candidate={r["candidate_id"]}',flush=True); continue
        print(f'[{branch} {idx:03d}/{total:03d}] start candidate={r["candidate_id"]} carrier={r["carrier_id"]} arm={r["probe_arm"]}',flush=True)
        try:
            z=np.load(work/r['data'],allow_pickle=False)
            if branch.startswith('stage_a'): info=simulate_stage_a(z['x'],z['x_reference'],c,out,mesh_rate_override=mesh_override)
            else: info=simulate_stage_b(z['x'],z['x_reference'],z['reference_lengths'],c,out,branch)
            done+=1
            print(f'[{branch} {idx:03d}/{total:03d}] done t={info.get("actual_t_final",0):.6g}/{info.get("target_t_final",0):.6g} ds_cv={info.get("max_ds_cv",0):.5f} stop={info.get("stop_reason")}'+(f' mesh/phys={info.get("max_mesh_to_physical_rms_ratio",0):.3f}' if branch.startswith('stage_a') else ''),flush=True)
        except Exception as e:
            errs.append({'candidate_id':r['candidate_id'],'error':repr(e)}); print(f'[{branch} {idx:03d}/{total:03d}] ERROR {e!r}',flush=True)
    s={'format':'SST-INTRINSIC-MODAL-RUN-2.1','branch':branch,'backend':backend_name(),'n_run':done,'n_errors':len(errs),'n_skipped_existing':skipped_existing,'n_skipped_unselected':skipped_unselected,'selected_carriers':len(selected) if selected is not None else None,'mesh_rate_override':mesh_override,'errors':errs,'gamma_canon_m2_s':GAMMA_CANON}
    (work/f'run_{branch}_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return s

def run_analyze_stage_a(work,config): return analyze_stage_a(work,cfg(config))
def run_analyze_stage_a_gauge(work,config): return analyze_stage_a_gauge(work,cfg(config))
def run_analyze_stage_b(work,config): return analyze_stage_b(work,cfg(config))
def reveal(work):
    work=Path(work); priv=json.loads((work/'private/reveal_map.json').read_text()); blind=json.loads((work/'analysis/blind_summary.json').read_text()) if (work/'analysis/blind_summary.json').exists() else {}; sa=json.loads((work/'analysis/blind_stage_a_summary.json').read_text()) if (work/'analysis/blind_stage_a_summary.json').exists() else {}; sg=json.loads((work/'analysis/blind_stage_a_gauge_summary.json').read_text()) if (work/'analysis/blind_stage_a_gauge_summary.json').exists() else {}
    out={'format':'SST-INTRINSIC-MODAL-REVEAL-2.1','blind_primary_gate':blind.get('primary_gate'),'blind_stage_a_gate':sa.get('primary_gate'),'blind_stage_a_gauge_gate':sg.get('primary_gate'),'secret_probe_flip':priv['secret_probe_flip'],'mapping':priv['rows']}
    (work/'analysis/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return out
