from __future__ import annotations
from pathlib import Path
import argparse,json,numpy as np
from experiment.source_loader import load_manifest_cases
from experiment.certification import full_certify_case
from experiment.mechanisms import elastic_raw, _core_force_one

def rel(a,b): return float(np.linalg.norm(np.asarray(a)-np.asarray(b))/max(np.linalg.norm(np.asarray(a)),1e-15))
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args();root=Path(a.root).resolve();out=root/'A054_Mechanism_Injection_Falsifier_v0.4.0-outputs';sel=json.loads((out/'MECHANISM_SELECTION_BLIND.json').read_text())['winner'];cfg=json.loads((root/'configs/mechanism_full.json').read_text());hard=json.loads((root/'configs/V020_HARD_GATES_FROZEN.json').read_text());rows=[]
 all_by_n={n:load_manifest_cases(root,'data/confirmation/CONFIRMATION_MANIFEST.json','data/confirmation',n=n) for n in hard['n_ladder']}
 byid={n:{x[0]:x[1] for x in xs} for n,xs in all_by_n.items()}; ids=sorted(byid[hard['n_ladder'][-1]])
 for cid in ids:
  per=[]
  for n in hard['n_ladder']:
   cc=byid[n][cid]
   for q,ga in {'Q0':[1,1,1],'Q1':[-1,1,1],'Q2':[1,-1,1],'Q3':[1,1,-1]}.items():
    met=full_certify_case(cc,ga,hard['core_ratio'],sel['arm'],sel['gain'],hard,cfg['core_shell']);per.append({'n':n,'sector':q,'metrics':met})
  rows.append({'case_id':cid,'rows':per})
 # strict convergence between final two N for any fine-grid recovered cell
 confirmed=0; unresolved_recovery=0
 for case in rows:
  for q in ('Q0','Q1','Q2','Q3'):
   rr=sorted([x for x in case['rows'] if x['sector']==q],key=lambda z:z['n']); m1,m2=rr[-2]['metrics'],rr[-1]['metrics']
   conv=(abs(m2['restoring_return_ratio_max']-m1['restoring_return_ratio_max'])<=float(hard['spatial_restoring_ratio_abs_max']) and abs(m2['kelvin_growth']-m1['kelvin_growth'])<=float(hard['spatial_kelvin_growth_abs_max']))
   if m2['recovered'] and conv: confirmed+=1
   if m2['recovered'] and not conv: unresolved_recovery+=1
 # native mechanism parity on fine-N confirmation geometries
 native_ok=False; parity=[]
 try:
  from experiment import native
  if native.available() and native.openmp_enabled():
   native_ok=True
   for cid in ids:
    cc=byid[hard['n_ladder'][-1]][cid]
    if sel['arm'] in ('ELASTIC','CORE_ELASTIC'):
     for c in cc: parity.append({'case_id':cid,'kernel':'elastic','rel_l2':rel(elastic_raw([c])[0],native.elastic_raw_native(c))})
    if sel['arm'] in ('CORE','CORE_ELASTIC'):
     kw=cfg['core_shell']
     for i,c in enumerate(cc):
      others=[x for j,x in enumerate(cc) if j!=i]; py=_core_force_one(i,cc,hard['core_ratio'],**kw); na=native.core_force_native(c,others,hard['core_ratio'],kw['sigma_rep_core'],kw['sigma_attr_core'],kw['attraction_fraction']); parity.append({'case_id':cid,'kernel':'core_force','rel_l2':rel(py,na)})
 except Exception as e:
  parity.append({'error':f'{type(e).__name__}: {e}'})
 parity_max=max([x['rel_l2'] for x in parity if 'rel_l2' in x],default=float('inf')); parity_pass=bool(native_ok and parity_max<=1e-10)
 result={'schema':'A054-V040-FULL-CERTIFICATION-1','selected':sel,'native_openmp':native_ok,'native_parity_max_rel_l2':parity_max,'native_parity_pass':parity_pass,'confirmed_converged_recovery_cells':confirmed,'unresolved_recovery_cells':unresolved_recovery,'pass':bool(parity_pass and confirmed>0 and unresolved_recovery==0),'rows':rows,'parity':parity,'rpo_floquet_status':'NOT_EVALUATED_UNLESS_RESTORING_KELVIN_RINGDOWN_CERTIFIED'}
 (out/'FULL_CERTIFICATION.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('rows','parity')},indent=2))
if __name__=='__main__': main()
