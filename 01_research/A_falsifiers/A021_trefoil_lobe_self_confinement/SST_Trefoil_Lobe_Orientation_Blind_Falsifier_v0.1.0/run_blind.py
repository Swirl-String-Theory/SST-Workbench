from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from sst_blind.experiment import run_campaign
from sst_blind.reporting import make_reports
DEFAULT_FSERIES=r"C:\workspace\projects\SST-Workbench\KnotPlot\Knots_FourierSeries\3_1\knot.3_1.fseries"
DEFAULT_KNOTPLOT=r"C:\workspace\projects\SST-Workbench\KnotPlot\knots\final\knot_3.1_final.txt"
def main():
    ap=argparse.ArgumentParser(description='Blind SST trefoil lobe-orientation / restoring-response falsifier')
    ap.add_argument('--fseries',default=DEFAULT_FSERIES);ap.add_argument('--knotplot',default=DEFAULT_KNOTPLOT);ap.add_argument('--config',default='configs/basic.json');ap.add_argument('--out-dir',default='outputs_blind')
    ap.add_argument('--backend',choices=['auto','openmp','cpu','sycl','python'],default='auto');ap.add_argument('--allow-sycl-cpu',action='store_true');ap.add_argument('--force-build',action='store_true');ap.add_argument('--build-verbose',action='store_true')
    a=ap.parse_args();final,results,mapping=run_campaign(fseries_path=a.fseries,knotplot_path=a.knotplot,config=a.config,out_dir=a.out_dir,backend=a.backend,allow_sycl_cpu=a.allow_sycl_cpu,force_build=a.force_build,build_verbose=a.build_verbose);make_reports(a.out_dir,final,results,mapping);print(json.dumps({'overall':final['overall'],'out_dir':a.out_dir,'blind_to_source':final['blind_to_source']},indent=2));return 0 if final['overall']!='INCONCLUSIVE' else 2
if __name__=='__main__':raise SystemExit(main())
