from pathlib import Path
import json
import numpy as np
from .blind import prepare,load_catalog
from .simulate import simulate_stage_a,simulate_stage_b
from .analyze import analyze_stage_a,analyze_stage_b
from .solver import backend_name
from .constants import GAMMA_CANON
from .util import clean_json

def cfg(path): return json.loads(Path(path).read_text())
def run_prepare(dataset,work,config): return prepare(dataset,work,cfg(config))

def _selected_stage_b_carriers(work):
    p=Path(work)/'analysis/stage_a_candidates.json'
    if not p.exists(): return set()
    data=json.loads(p.read_text(encoding='utf-8')); return {r['carrier_id'] for r in data.get('candidates',[])}

def run_branch(work,config,branch,limit=None):
    work=Path(work); c=cfg(config); rows=load_catalog(work); selected=None
    if branch in ('material','fixed'): selected=_selected_stage_b_carriers(work)
    od=work/f'results_{branch}/candidates'; od.mkdir(parents=True,exist_ok=True); errs=[]; done=0; skipped_existing=0; skipped_unselected=0
    for r in rows[:limit or None]:
        if selected is not None and r['carrier_id'] not in selected:
            skipped_unselected+=1; continue
        out=od/f'{r["candidate_id"]}.npz'
        if out.exists(): skipped_existing+=1; continue
        try:
            z=np.load(work/r['data'],allow_pickle=False)
            if branch=='stage_a': simulate_stage_a(z['x'],z['x_reference'],c,out)
            else: simulate_stage_b(z['x'],z['x_reference'],z['reference_lengths'],c,out,branch)
            done+=1
        except Exception as e: errs.append({'candidate_id':r['candidate_id'],'error':repr(e)})
    s={'format':'SST-INTRINSIC-MODAL-RUN-2.0','branch':branch,'backend':backend_name(),'n_run':done,'n_errors':len(errs),'n_skipped_existing':skipped_existing,'n_skipped_unselected':skipped_unselected,'selected_stage_b_carriers':len(selected) if selected is not None else None,'errors':errs,'gamma_canon_m2_s':GAMMA_CANON}
    (work/f'run_{branch}_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return s

def run_analyze_stage_a(work,config): return analyze_stage_a(work,cfg(config))
def run_analyze_stage_b(work,config): return analyze_stage_b(work,cfg(config))
def reveal(work):
    work=Path(work); priv=json.loads((work/'private/reveal_map.json').read_text()); blind=json.loads((work/'analysis/blind_summary.json').read_text()) if (work/'analysis/blind_summary.json').exists() else {}
    sa=json.loads((work/'analysis/blind_stage_a_summary.json').read_text()) if (work/'analysis/blind_stage_a_summary.json').exists() else {}
    out={'format':'SST-INTRINSIC-MODAL-REVEAL-2.0','blind_primary_gate':blind.get('primary_gate'),'blind_stage_a_gate':sa.get('primary_gate'),'secret_probe_flip':priv['secret_probe_flip'],'mapping':priv['rows']}
    (work/'analysis/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return out
