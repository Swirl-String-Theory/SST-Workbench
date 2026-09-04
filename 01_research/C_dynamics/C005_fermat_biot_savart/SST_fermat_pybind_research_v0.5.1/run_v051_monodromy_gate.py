#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from fermat_ext.core import write_json

def main()->int:
 p=argparse.ArgumentParser(description='Hard monodromy gate report for v0.5.1 selected-convergence output.'); p.add_argument('--input',required=True); p.add_argument('--out',default='monodromy_gate.json'); a=p.parse_args()
 data=json.loads(Path(a.input).read_text(encoding='utf-8')); rows=[]
 for k,v in data.get('results',{}).items():
  conv=v.get('convergence'); certified=bool(conv and conv.get('global_closed_orbit_certified'))
  rows.append({'knot_id':k,'global_closed_orbit_certified':certified,'monodromy_action':'ELIGIBLE_FOR_MONODROMY' if certified else 'SKIPPED_GLOBAL_ORBIT_NOT_CERTIFIED'})
 result={'schema':'sst.fermat.monodromy-hard-gate.v0.5.1','rows':rows,'eligible_count':sum(r['global_closed_orbit_certified'] for r in rows),'monodromy_certified':False,'qsm_certified':False}; write_json(a.out,result); print(json.dumps(result,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
