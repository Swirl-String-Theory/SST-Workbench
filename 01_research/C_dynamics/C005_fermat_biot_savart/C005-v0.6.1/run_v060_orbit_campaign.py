#!/usr/bin/env python3
from __future__ import annotations
import argparse,subprocess,sys,json,shutil,zipfile
from pathlib import Path
from fermat_ext.core import write_json

def run(cmd,root,log):
 with log.open('w',encoding='utf-8') as f:
  p=subprocess.Popen(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
  for line in p.stdout: print(line,end=''); f.write(line)
  return p.wait()
def main()->int:
 p=argparse.ArgumentParser(); p.add_argument('--preset',choices=['smoke','full'],default='full'); p.add_argument('--out-root',default='v0.6.1_campaign_output'); p.add_argument('--archive',default='SST_fermat_pybind_research_v0.6.1_results.zip'); p.add_argument('--require-native',action='store_true'); p.add_argument('--overwrite',action='store_true'); a=p.parse_args()
 root=Path(__file__).resolve().parent; out=root/a.out_root
 if a.overwrite: shutil.rmtree(out,ignore_errors=True)
 out.mkdir(parents=True,exist_ok=True); (out/'logs').mkdir(exist_ok=True)
 if a.preset=='smoke':
  cmd=[sys.executable,'run_multistart_shooting.py','--knots','0_1','--centerline-points','2048','--stations','1','--angles','3','--period-multipliers','1','--coarse-steps','24','--coarse-iterations','0','--refine-top-k','1','--refine-steps','24','--refine-iterations','0','--out-dir',str(out/'multistart_smoke')]
  rc=run(cmd,root,out/'logs/01_multistart_smoke.log'); expected=out/'multistart_smoke/multistart.json'
  scientific={'global_closed_orbit_certified':False,'monodromy_certified':False,'qsm_certified':False}
 else:
  cmd=[sys.executable,'run_v060_selected_convergence.py','--knots','0_1','3_1','4_1','5_2','--selection-centerline-points','8192','--centerline-point-counts','8192','16384','32768','--step-counts','256','512','1024','--stations','4','--angles','8','--period-multipliers','.5','1','2','4','8','--max-iterations','12','--out-dir',str(out/'selected_convergence')]
  if a.require_native: cmd.append('--require-native')
  rc=run(cmd,root,out/'logs/01_selected_convergence.log'); expected=out/'selected_convergence/selected_convergence.json'
  scientific={'global_closed_orbit_certified':False,'monodromy_certified':False,'qsm_certified':False}
 status='SUCCESS' if rc==0 and expected.exists() else 'FAILED'
 summary={'schema':'sst.fermat.v0.6.1-campaign-summary','preset':a.preset,'status':status,**scientific}; write_json(out/'campaign_summary.json',summary)
 if status=='SUCCESS':
  with zipfile.ZipFile(root/a.archive,'w',zipfile.ZIP_DEFLATED) as z:
   for f in sorted(out.rglob('*')):
    if f.is_file(): z.write(f,(Path(out.name)/f.relative_to(out)).as_posix())
 print(json.dumps(summary,indent=2)); return 0 if status=='SUCCESS' else 2
if __name__=='__main__': raise SystemExit(main())
