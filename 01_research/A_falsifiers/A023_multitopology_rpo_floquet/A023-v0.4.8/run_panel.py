from __future__ import annotations
import argparse, json
from pathlib import Path
from sst_blind.multitopology import run_panel

ROOT=Path(__file__).resolve().parent
PANEL=ROOT/'repro_inputs'/'panel'

def canonical_entries():
    def kp(stem,cls):
        return dict(source=stem,kind='knotplot',topology_class=cls,path=str(PANEL/f'{stem}_final.txt'),metrics_path=str(PANEL/f'{stem}_final.metrics.json'))
    def fr(name,label,cls='knot'):
        return dict(source=label,kind='fseries',topology_class=cls,path=str(PANEL/f'fremlin_knot.{name}.fseries'))
    return [
      fr('1_1','fremlin_0_1','unknot'), kp('knot_0.1','unknot'),
      fr('3_1','fremlin_3_1'), kp('knot_3.1','knot'), kp('torus_2.3','torus_knot'),
      fr('4_1','fremlin_4_1'), kp('knot_4.1','knot'),
      fr('5_1','fremlin_5_1'), kp('knot_5.1','knot'),
      fr('5_2','fremlin_5_2'), kp('knot_5.2','knot'),
      kp('link_0.2.1','unlink'), kp('link_0.3.1','unlink'), kp('link_2.2.1','link'),
      kp('link_6.3.1','link'), kp('link_6.3.3','link'), kp('torus_6.9','torus_link'),
    ]

def main():
    ap=argparse.ArgumentParser(description='SST v0.4.8 blind multi-topology knot/link TBK + RPO comparative panel')
    ap.add_argument('--config',default='configs/panel_basic.json');ap.add_argument('--out-dir',default='outputs_panel_basic');ap.add_argument('--backend',choices=['auto','openmp','cpu','sycl','sycl-fp32','sycl-dd32','sycl-fp64','python'],default='auto');ap.add_argument('--allow-sycl-cpu',action='store_true');ap.add_argument('--force-build',action='store_true');ap.add_argument('--build-verbose',action='store_true')
    a=ap.parse_args();f,_,m=run_panel(canonical_entries(),a.config,a.out_dir,backend=a.backend,allow_sycl_cpu=a.allow_sycl_cpu,force_build=a.force_build,build_verbose=a.build_verbose);print(json.dumps({'overall':f['overall'],'datasets':f['dataset_count'],'out_dir':a.out_dir,'blind_to_source':{b:x['source'] for b,x in m.items()}},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
