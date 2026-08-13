from __future__ import annotations
import argparse,json
from pathlib import Path
from .audits import run_demo,audit_t02_holonomy,audit_t04_exterior_hodge,audit_t05_energy_helicity,audit_t07_radial_flux
from .geometry import load_curve,resample_closed
from .reporting import write_reports
from .constants import GAMMA0

def main(argv=None):
    p=argparse.ArgumentParser(prog='maxwell-sst',description='Seven Maxwell-inspired SST falsification/audit routes')
    sub=p.add_subparsers(dest='cmd',required=True)
    d=sub.add_parser('demo'); d.add_argument('--out',default='outputs_demo')
    c=sub.add_parser('centerline'); c.add_argument('path'); c.add_argument('--out',default='outputs_centerline'); c.add_argument('--gamma',type=float,default=GAMMA0); c.add_argument('--core-a',type=float,default=None); c.add_argument('--resample',type=int,default=400)
    args=p.parse_args(argv)
    if args.cmd=='demo':
        results=run_demo(None)
    else:
        curve=resample_closed(load_curve(args.path),args.resample)
        results=[audit_t02_holonomy(curve,args.gamma,args.core_a),audit_t04_exterior_hodge(curve,1.7,args.core_a),audit_t05_energy_helicity(curve,args.core_a),audit_t07_radial_flux(curve,args.core_a)]
    path=write_reports(results,args.out)
    print(path)
    for r in results: print(f"{r['id']}: {r['status']}  {r['name']}")
    return 0

if __name__=='__main__': raise SystemExit(main())
