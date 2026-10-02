from pathlib import Path
import json
import numpy as np
from .blind import prepare,load_catalog
from .simulate import simulate
from .analyze import analyze
from .solver import backend_name
from .constants import GAMMA_CANON
from .util import clean_json

def cfg(path): return json.loads(Path(path).read_text())
def run_prepare(dataset,work,config): return prepare(dataset,work,cfg(config))
def run_branch(work,config,branch,limit=None):
    work=Path(work); c=cfg(config); rows=load_catalog(work); od=work/f'results_{branch}/candidates'; od.mkdir(parents=True,exist_ok=True); errs=[]; done=0
    for r in rows[:limit or None]:
        out=od/f'{r["candidate_id"]}.npz'
        if out.exists(): continue
        try:
            z=np.load(work/r['data'],allow_pickle=False); simulate(z['x'],z['x_reference'],z['reference_lengths'],c,out,branch); done+=1
        except Exception as e: errs.append({'candidate_id':r['candidate_id'],'error':repr(e)})
    s={'format':'SST-INTRINSIC-MODAL-RUN-1.0','branch':branch,'backend':backend_name(),'n_run':done,'n_errors':len(errs),'errors':errs,'gamma_canon_m2_s':GAMMA_CANON}
    (work/f'run_{branch}_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return s
def run_analyze(work,config): return analyze(work,cfg(config))
def reveal(work):
    work=Path(work); priv=json.loads((work/'private/reveal_map.json').read_text()); blind=json.loads((work/'analysis/blind_summary.json').read_text())
    out={'format':'SST-INTRINSIC-MODAL-REVEAL-1.0','blind_primary_gate':blind.get('primary_gate'),'secret_probe_flip':priv['secret_probe_flip'],'mapping':priv['rows']}
    (work/'analysis/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True)+'\n',encoding='utf-8'); return out
