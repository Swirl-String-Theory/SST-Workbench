#!/usr/bin/env python3
from __future__ import annotations
import argparse,subprocess,sys,shutil,json,zipfile
from pathlib import Path
from fermat_ext.core import write_json

def run(cmd,root,log):
 with log.open('w',encoding='utf-8') as f:
  p=subprocess.Popen(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
  for line in p.stdout: print(line,end=''); f.write(line)
  return p.wait()
def main():
 p=argparse.ArgumentParser(); p.add_argument('--preset',choices=['smoke','full'],default='full'); p.add_argument('--out-root',default='v0.6.1_campaign_output'); p.add_argument('--archive',default='SST_fermat_pybind_research_v0.6.1_results.zip'); p.add_argument('--require-native',action='store_true'); p.add_argument('--overwrite',action='store_true'); a=p.parse_args()
 root=Path(__file__).resolve().parent; out=root/a.out_root
 if a.overwrite: shutil.rmtree(out,ignore_errors=True)
 out.mkdir(parents=True,exist_ok=True); (out/'logs').mkdir(exist_ok=True)
 if a.preset=='smoke': points=512; rr=['.75','1.0']; gr=['-.5','0','.5']
 else: points=8192; rr=['.5','.75','1','1.25','1.5','2']; gr=['-2','-1','-.5','0','.5','1','2']
 cmd=[sys.executable,'run_hole_bundle_sweep.py','--knot','3_1','--centerline-points',str(points),'--radius-ratios',*rr,'--circulation-ratios',*gr,'--out-dir',str(out/'hole_bundle_sweep')]
 if a.require_native: cmd.append('--require-native')
 rc=run(cmd,root,out/'logs/01_hole_bundle_sweep.log')
 expected=out/'hole_bundle_sweep/hole_bundle_sweep.json'; status='SUCCESS' if rc==0 and expected.exists() else 'FAILED'
 summary={'schema':'sst.fermat.v0.6.1-campaign-summary','status':status,'preset':a.preset,'hole_bundle_sweep_completed':status=='SUCCESS','physical_finite_closed_bundle_certified':False,'global_closed_orbit_certified':False,'qsm_certified':False}; write_json(out/'campaign_summary.json',summary)
 if status=='SUCCESS':
  with zipfile.ZipFile(root/a.archive,'w',zipfile.ZIP_DEFLATED) as z:
   for f in sorted(out.rglob('*')):
    if f.is_file(): z.write(f,(Path(out.name)/f.relative_to(out)).as_posix())
 print(json.dumps(summary,indent=2)); return 0 if status=='SUCCESS' else 2
if __name__=='__main__': raise SystemExit(main())
