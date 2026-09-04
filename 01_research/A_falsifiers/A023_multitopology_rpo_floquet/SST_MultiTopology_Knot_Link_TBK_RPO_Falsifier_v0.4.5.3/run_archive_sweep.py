from __future__ import annotations
import argparse, json
from run_archive_campaign import all_entries
from sst_blind.multitopology import run_panel

def main():
    ap=argparse.ArgumentParser(description='v0.4.5.3 quick survey over all 127 archive geometry files')
    ap.add_argument('--config',default='configs/panel_survey.json'); ap.add_argument('--out-dir',default='outputs_archive_survey')
    ap.add_argument('--backend',default='auto',choices=['auto','openmp','cpu','sycl','python']); ap.add_argument('--allow-sycl-cpu',action='store_true')
    a=ap.parse_args(); e=all_entries(); f,_,_=run_panel(e,a.config,a.out_dir,backend=a.backend,allow_sycl_cpu=a.allow_sycl_cpu)
    print(json.dumps({'datasets':len(e),'overall':f['overall'],'out_dir':a.out_dir},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
