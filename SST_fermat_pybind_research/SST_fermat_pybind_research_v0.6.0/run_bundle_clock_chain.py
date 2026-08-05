#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from fermat_ext.core import write_json
from fermat_ext.hole_bundle import HoleBundleParameters,clock_chain

def main():
 p=argparse.ArgumentParser(); p.add_argument('--bundle-radius',type=float,required=True); p.add_argument('--return-radius',type=float,required=True); p.add_argument('--circulation-ratio',type=float,required=True); p.add_argument('--reference-omega',type=float,default=1.0); p.add_argument('--out',default='bundle_clock_chain.json'); a=p.parse_args()
 b=HoleBundleParameters(a.bundle_radius,a.return_radius,a.circulation_ratio); result={'schema':'sst.fermat.bundle-clock-chain.v0.6.0','bundle':b.__dict__,'chain':clock_chain(b,reference_omega_over_c_per_rc=a.reference_omega),'status':'RESEARCH_TRACK_BRIDGE','proper_time_certified':False}; write_json(a.out,result); print(json.dumps(result,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
