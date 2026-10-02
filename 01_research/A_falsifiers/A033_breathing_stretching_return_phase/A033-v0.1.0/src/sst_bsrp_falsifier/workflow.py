from pathlib import Path
import json,hashlib
import numpy as np
from .blind import prepare,load_catalog
from .simulate import simulate
from .analyze import analyze
from .solver import backend_name
from .constants import GAMMA_CANON,R_C,V_SWIRL
from .util import clean_json

def readcfg(path): return json.loads(Path(path).read_text(encoding='utf-8'))

def run_prepare(dataset,work,config): return prepare(dataset,work,readcfg(config))

def run_candidates(work,config,limit=None):
    work=Path(work); cfg=readcfg(config); cat=load_catalog(work); (work/'results/candidates').mkdir(parents=True,exist_ok=True)
    done=0; errs=[]
    for r in cat[:limit or None]:
        out=work/'results/candidates'/f"{r['candidate_id']}.npz"
        if out.exists(): continue
        try:
            z=np.load(work/r['data'],allow_pickle=False); x=z['x'] if hasattr(z,'files') and 'x' in z.files else z; refs=(z['reference_lengths'] if hasattr(z,'files') and 'reference_lengths' in z.files else None)
            simulate(x,cfg,out,reference_lengths=refs,dt_reference_ds=r.get('dt_reference_ds')); done+=1
        except Exception as e: errs.append({'candidate_id':r['candidate_id'],'error':repr(e)})
    s={'format':'SST-BSRP-RUN-1.0','backend':backend_name(),'n_run':done,'n_errors':len(errs),'errors':errs,'gamma_canon_m2_s':GAMMA_CANON,'r_c_m':R_C,'v_swirl_m_s':V_SWIRL}
    (work/'run_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8'); return s

def run_analyze(work,config): return analyze(work,readcfg(config))

def reveal(work):
    work=Path(work); priv=json.loads((work/'private/reveal_map.json').read_text()); blind=json.loads((work/'results/blind_summary.json').read_text()) if (work/'results/blind_summary.json').exists() else {}
    out={'format':'SST-BSRP-REVEAL-1.0','secret_packet_flip':priv['secret_packet_flip'],'secret_breath_flip':priv['secret_breath_flip'],'blind_verdict':blind.get('primary_phase_causality_gate'),'private_key_commitment_sha256':hashlib.sha256(json.dumps(priv,sort_keys=True,indent=2).encode()).hexdigest(),'mapping':priv['rows']}
    (work/'results/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    md=['# BSRP reveal','',f"Blind primary gate: **{out['blind_verdict']}**",'',f"Packet anonymous sign flip → physical polarity: `{out['secret_packet_flip']:+d}`",f"Breathing anonymous sign flip → physical sign: `{out['secret_breath_flip']:+d}`",'', 'The semantic mapping was not used by the blind simulation or primary scoring path.']
    (work/'results/RESULTS_SUMMARY.md').write_text('\n'.join(md)+'\n',encoding='utf-8'); return out
