from __future__ import annotations
import argparse,json
from collections import defaultdict
import numpy as np
from .common import read_csv,load_json,dump_json,cv,relerr,logfit

def main():
 p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args();rows=read_csv(a.csv);cfg=load_json(a.config)['closure'];out={'format':'SST-WP-FIELD-MATTER-CLOSURE-2.0','n':len(rows),'gates':{},'metrics':{},'nonclaims':[]}
 # Wien similarity if scale_a/omega exist
 sim=[float(r['scale_a'])**2*float(r['omega_rad_s']) for r in rows if r.get('scale_a') and r.get('omega_rad_s')];out['metrics']['similarity_cv']=cv(sim) if sim else None;out['gates']['A_Wien_similarity']=bool(sim) and cv(sim)<=cfg['similarity_cv_max']
 me=[relerr(float(r['M_E_kg']),float(r['M_I_kg'])) for r in rows if r.get('M_E_kg') and r.get('M_I_kg')];out['metrics']['mass_error_max']=max(me) if me else None;out['gates']['B1_energy_inertial_mass']=bool(me) and max(me)<=cfg['mass_equivalence_rel_tol']
 gr=[float(r['C_p'])/float(r['M_I_kg']) for r in rows if r.get('C_p') and r.get('M_I_kg')];out['metrics']['Cp_over_MI_cv']=cv(gr) if gr else None;out['gates']['B2_pressure_monopole_universality']=bool(gr) and cv(gr)<=cfg['gravity_ratio_cv_max']
 be=[relerr(float(r['beta_knot']),float(r['beta_fluid'])) for r in rows if r.get('beta_knot') and r.get('beta_fluid')];out['metrics']['beta_error_max']=max(be) if be else None;out['gates']['D1_field_matter_beta_closure']=bool(be) and max(be)<=cfg['beta_rel_tol']
 dr=[abs(float(r['energy_drift_rel'])) for r in rows if r.get('energy_drift_rel')];out['metrics']['energy_drift_max']=max(dr) if dr else None;out['gates']['D2_energy_conservation']=bool(dr) and max(dr)<=cfg['energy_drift_rel_max']
 out['pass']=all(out['gates'].values());out['nonclaims']=['B1/B2 require independently generated inertial/pressure observables; the line-filament action campaign does not synthesize them.','D1 is coarse-grained statistical closure, not microscopic entropy production in ideal Euler flow.']
 dump_json(a.out,out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
