from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from .audits import run_demo,audit_t02_holonomy,audit_t04_exterior_hodge,audit_t05_energy_helicity,audit_t07_radial_flux
from .geometry import load_curve_set,resample_closed
from .reporting import write_test_reports
from .batch import run_batch
from .constants import GAMMA0
from native_ext import backend_info,set_num_threads

def main(argv=None):
    p=argparse.ArgumentParser(prog='4-maxwell-sst',description='4_ SST Maxwell workbench v0.2.0')
    sub=p.add_subparsers(dest='cmd',required=True)
    d=sub.add_parser('demo'); d.add_argument('--out',default='4_outputs_demo')
    c=sub.add_parser('centerline'); c.add_argument('path'); c.add_argument('--out',default='4_outputs_centerline'); c.add_argument('--resample',type=int,default=400); c.add_argument('--native-threads',type=int,default=16)
    b=sub.add_parser('batch'); b.add_argument('--input',required=True); b.add_argument('--out',default=None); b.add_argument('--preset',choices=['basic','extended'],default='basic'); b.add_argument('--native-threads',type=int,default=16); b.add_argument('--ids',default=None)
    n=sub.add_parser('native-info')
    args=p.parse_args(argv)
    if args.cmd=='native-info': print(json.dumps(backend_info(),indent=2)); return 0
    if args.cmd=='demo': results=run_demo(); path=write_test_reports(results,args.out,{'backend':backend_info()})
    elif args.cmd=='centerline':
        set_num_threads(args.native_threads); cs=load_curve_set(args.path); comps=[resample_closed(x,args.resample) for x in cs.components]; results=[audit_t02_holonomy(comps,[GAMMA0]*len(comps)),audit_t04_exterior_hodge(comps),audit_t05_energy_helicity(comps),audit_t07_radial_flux(comps)]; path=write_test_reports(results,args.out,{'file':str(cs.path),'components':len(comps),'backend':backend_info()})
    else: path=run_batch(args.input,args.out,args.preset,args.native_threads,args.ids)
    print(path); return 0
if __name__=='__main__': raise SystemExit(main())
