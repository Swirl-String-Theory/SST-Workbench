#!/usr/bin/env python3
"""Produce audit-safe importable gate evidence; NOT a replacement for framework runtime."""
import argparse,json
from pathlib import Path
from gp_full_xpu import json_exclusive,sha256

def transform(r):
    g=r['g32_screen']['all_preconditions_met']
    parity=r['cpu_fp64_parity']
    return {'schema':'A069-V063-FRAMEWORK-1.0.10-GATE-EVIDENCE-1',
     'target_framework':'1.0.10','framework_executed':False,
     'science_run_schema':r['schema'],
     'evaluations':{
      'G32':{'status':'PASS' if g else 'FAIL','execution_status':'EXECUTED',
             'qualification':'DIAGNOSTIC_ONLY','reason':'mesh and source geometry screen, not dynamics certification'},
      'G33':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
             'qualification':'UNRESOLVED','reason':'offline topological detector required'},
      'G34':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
             'qualification':'UNRESOLVED','reason':'no certified continuous knot transport or isotopy'},
      'G35':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED',
             'qualification':'BLOCKED_PREREQUISITE','blocked_by':['G34'],
             'reason':'no stable relative equilibrium or independent mode'},
      'GPU_PARITY_DIAGNOSTIC':{'status':'PASS' if parity['status']=='PASS_NUMERICAL_SCREENING' else ('FAIL' if parity['status']=='FAIL_PARITY' else 'UNRESOLVED'),
         'execution_status':parity['execution_status'],'qualification':'DIAGNOSTIC_ONLY'}},
     'G9_reveal_eligibility':'BLOCKED','physical_claims':False,
     'warning':'This output is NOT an official framework-signed ledger or certified blind run.'}

def main():
 p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=json.loads(a.result.read_text());obj=transform(r);obj['source_json_sha256']=sha256(a.result)
 json_exclusive(a.out,obj)
 print(a.out)
if __name__=='__main__':main()
