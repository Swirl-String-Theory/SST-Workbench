from pathlib import Path
import json
import numpy as np
from .blind import prepare,prepare_provenance,scan_provenance,load_catalog
from .simulate import simulate_stage_a,simulate_stage_b
from .analyze import analyze_stage_a,analyze_stage_a_gauge,analyze_stage_b,analyze_provenance
from .solver import backend_name
from .constants import GAMMA_CANON
from .util import clean_json

def cfg(path): return json.loads(Path(path).read_text())
def run_prepare(dataset,work,config): return prepare(dataset,work,cfg(config))
def run_prepare_provenance(work,config): return prepare_provenance(work,cfg(config),config_base=Path.cwd())
def run_scan_provenance(config): return scan_provenance(cfg(config),config_base=Path.cwd())

def _candidate_carriers(work,provisional=False):
    name='stage_a_candidates_provisional.json' if provisional else 'stage_a_candidates.json';p=Path(work)/'analysis'/name
    if not p.exists(): return set()
    data=json.loads(p.read_text(encoding='utf-8'));return {r['carrier_id'] for r in data.get('candidates',[])}

def _branch_spec(branch,c):
    if branch=='stage_a': return 'stage_a',None,None,None
    if branch in ('stage_a_gauge_low','stage_a_gauge_high'):
        factor=float(c.get('mesh_gauge_low_factor',.7) if branch.endswith('low') else c.get('mesh_gauge_high_factor',1.3));return branch,_candidate_carriers,float(c.get('mesh_redistribution_rate',4.0))*factor,float(c.get('mesh_max_relative_rms',2.0))*factor
    return branch,_candidate_carriers,None,None

def run_branch(work,config,branch,limit=None):
    work=Path(work);c=cfg(config);rows=load_catalog(work);selected=None;outbranch,selector,mesh_override,cap_override=_branch_spec(branch,c)
    if branch in ('stage_a_gauge_low','stage_a_gauge_high'): selected=_candidate_carriers(work,provisional=True)
    elif branch in ('material','fixed'): selected=_candidate_carriers(work,provisional=False)
    od=work/f'results_{outbranch}/candidates';od.mkdir(parents=True,exist_ok=True);errs=[];done=0;skipped_existing=0;skipped_unselected=0;todo=[]
    for r in rows[:limit or None]:
        if selected is not None and r['carrier_id'] not in selected: skipped_unselected+=1;continue
        todo.append(r)
    total=len(todo)
    for idx,r in enumerate(todo,1):
        out=od/f'{r["candidate_id"]}.npz'
        if out.exists(): skipped_existing+=1;print(f'[{branch} {idx:03d}/{total:03d}] skip existing candidate={r["candidate_id"]}',flush=True);continue
        print(f'[{branch} {idx:03d}/{total:03d}] start candidate={r["candidate_id"]} carrier={r["carrier_id"]} arm={r["probe_arm"]} comps={r.get("n_components",1)}',flush=True)
        try:
            z=np.load(work/r['data'],allow_pickle=False);offsets=np.asarray(z['component_offsets'],dtype=np.int64) if 'component_offsets' in z.files else np.asarray([0,len(z['x'])],dtype=np.int64)
            if branch.startswith('stage_a'): info=simulate_stage_a(z['x'],z['x_reference'],c,out,mesh_rate_override=mesh_override,mesh_cap_override=cap_override,component_offsets=offsets)
            else: info=simulate_stage_b(z['x'],z['x_reference'],z['reference_lengths'],c,out,branch,component_offsets=offsets)
            done+=1;print(f'[{branch} {idx:03d}/{total:03d}] done t={info.get("actual_t_final",0):.6g}/{info.get("target_t_final",0):.6g} ds_cv={info.get("max_ds_cv",0):.5f} stop={info.get("stop_reason")}'+(f' mesh/phys={info.get("max_mesh_to_physical_rms_ratio",0):.3f}' if branch.startswith('stage_a') else ''),flush=True)
        except Exception as e: errs.append({'candidate_id':r['candidate_id'],'error':repr(e)});print(f'[{branch} {idx:03d}/{total:03d}] ERROR {e!r}',flush=True)
    s={'format':'SST-INTRINSIC-MODAL-RUN-2.2','branch':branch,'backend':backend_name(),'n_run':done,'n_errors':len(errs),'n_skipped_existing':skipped_existing,'n_skipped_unselected':skipped_unselected,'selected_carriers':len(selected) if selected is not None else None,'mesh_rate_override':mesh_override,'mesh_cap_override':cap_override,'errors':errs,'gamma_canon_m2_s':GAMMA_CANON}
    (work/f'run_{branch}_summary.json').write_text(json.dumps(clean_json(s),indent=2,sort_keys=True)+'\n',encoding='utf-8');return s

def run_analyze_stage_a(work,config): return analyze_stage_a(work,cfg(config))
def run_analyze_stage_a_gauge(work,config): return analyze_stage_a_gauge(work,cfg(config))
def run_analyze_provenance(work,config): return analyze_provenance(work,cfg(config))
def run_analyze_stage_b(work,config): return analyze_stage_b(work,cfg(config))
def reveal(work):
    work=Path(work);priv=json.loads((work/'private/reveal_map.json').read_text());blind=json.loads((work/'analysis/blind_summary.json').read_text()) if (work/'analysis/blind_summary.json').exists() else {};sa=json.loads((work/'analysis/blind_stage_a_summary.json').read_text()) if (work/'analysis/blind_stage_a_summary.json').exists() else {};sg=json.loads((work/'analysis/blind_stage_a_gauge_summary.json').read_text()) if (work/'analysis/blind_stage_a_gauge_summary.json').exists() else {};sp=json.loads((work/'analysis/blind_provenance_summary.json').read_text()) if (work/'analysis/blind_provenance_summary.json').exists() else {}
    out={'format':'SST-INTRINSIC-MODAL-REVEAL-2.2','blind_primary_gate':blind.get('primary_gate'),'blind_stage_a_gate':sa.get('primary_gate'),'blind_stage_a_gauge_gate':sg.get('primary_gate'),'blind_provenance_gate':sp.get('primary_gate'),'secret_probe_flip':priv['secret_probe_flip'],'mapping':priv['rows']}
    (work/'analysis/reveal.json').write_text(json.dumps(clean_json(out),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    # Convenience revealed provenance join; primary scoring never reads this.
    import csv
    bp=work/'analysis/blind_provenance_results.csv'
    if bp.exists():
        by_carrier={}
        for r in priv['rows']:
            by_carrier.setdefault(r['carrier_id'],r)
        revealed=[]
        with open(bp,newline='',encoding='utf-8') as f:
            for row in csv.DictReader(f):
                try: vm=json.loads(row.get('variant_metrics','[]'))
                except Exception: vm=[]
                for v in vm:
                    meta=by_carrier.get(v.get('carrier_id',''),{}); v.update({'topology_id':meta.get('topology_id'),'provenance':meta.get('provenance'),'source_name':meta.get('source_name'),'source_record_id':meta.get('source_record_id')})
                row['variant_metrics']=vm
                if vm: row['topology_id']=vm[0].get('topology_id')
                revealed.append(row)
        (work/'analysis/revealed_provenance_results.json').write_text(json.dumps(clean_json(revealed),indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return out
