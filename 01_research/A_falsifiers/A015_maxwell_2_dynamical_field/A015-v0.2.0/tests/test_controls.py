from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def run(name):
    p=subprocess.run([sys.executable,str(ROOT/'run_blind.py'),'--campaign',str(ROOT/'examples'/name)],capture_output=True,text=True)
    result=json.loads((ROOT/'examples'/name/'frozen_result.json').read_text())
    return p.returncode,result

def main():
    subprocess.run([sys.executable,str(ROOT/'make_synthetic_controls.py')],check=True)
    code,r=run('positive_control'); assert code==0 and r['overall_status']=='PASS'
    code,r=run('negative_transverse'); assert code==2 and next(g for g in r['gates'] if g['gate']=='DFC-T')['status']=='FAIL'
    code,r=run('negative_displacement'); assert code==2 and next(g for g in r['gates'] if g['gate']=='DFC-D')['status']=='FAIL'
    code,r=run('negative_gravity'); assert code==2 and next(g for g in r['gates'] if g['gate']=='DFC-G')['status']=='FAIL'
    print('PASS: positive and three gate-specific negative controls behave as preregistered')

if __name__=='__main__': main()
