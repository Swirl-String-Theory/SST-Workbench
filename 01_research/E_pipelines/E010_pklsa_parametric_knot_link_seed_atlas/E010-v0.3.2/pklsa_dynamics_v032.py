#!/usr/bin/env python3
"""Versioned E010 v0.3.2 dynamics qualifier, consuming E011 v0.3.0 unchanged."""
from __future__ import annotations
import argparse,json,sys,hashlib,datetime,secrets
from pathlib import Path
from pklsa_builder.dynamics_ready import (E011SeedContract,AdmissionError,native_geometry,
      qualify,sha256_file,canonical_json_file,MODEL_ID,SCHEMA)

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--workbench',required=True,help='SST-Workbench root (source bytes)')
 p.add_argument('--e011',required=True,help='Unchanged E011 STATIC_READY outputs ZIP or directory')
 p.add_argument('--e010',help='Unchanged E010 results ZIP for dependency hash; recommended')
 p.add_argument('--expected-e011-sha',default='97cd1acbf23c102e4564f2d74fd329a2d03f32a29b8bd376ffa8b806c14246cc',help='Pinned upstream E011 ZIP SHA256')
 p.add_argument('--expected-e010-sha',default='b9036620c130b1a2a89b1b0a98c0e088bf2d9b32a661781598806ff40cbfad6b',help='Pinned upstream E010 ZIP SHA256')
 p.add_argument('--topology',default='3_1')
 p.add_argument('--provider',default='gilbert')
 p.add_argument('--source-override',help='Explicit source location only if raw SHA matches E011')
 p.add_argument('--fine-n',type=int,default=256)
 p.add_argument('--steps',type=int,default=8)
 p.add_argument('--t-final',type=float,default=0.004)
 p.add_argument('--core',type=float,default=0.017)
 p.add_argument('--basic',action='store_true',help='small diagnostic run; never DYNAMICS_READY')
 p.add_argument('--out',required=True)
 args=p.parse_args(argv)
 out=Path(args.out).resolve()
 if out.suffix.lower() != '.json':
  out=out/(f"{args.topology}_{args.provider}_{'BASIC' if args.basic else 'FULL'}_"
          f"{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}_"
          f"{secrets.token_hex(3)}_RUN_RESULT.json")
 try:
  e011=E011SeedContract(args.e011,args.expected_e011_sha)
  e010_hash=None
  if args.e010:
   if not Path(args.e010).is_file():raise AdmissionError('E010 dependency ZIP not found')
   e010_hash=sha256_file(Path(args.e010))
   if args.expected_e010_sha and e010_hash!=args.expected_e010_sha:raise AdmissionError('E010 dependency SHA mismatch')
  elif args.expected_e010_sha:raise AdmissionError('Pinned E010 SHA without --e010 ZIP')
  seed=e011.select(args.topology,args.provider)
  points,source=native_geometry(seed,args.workbench,args.source_override,n_original=max(args.fine_n*4,1024))
  result=qualify(points,core=args.core,tfinal=args.t_final,steps=args.steps,
                 fine_n=args.fine_n,full=not args.basic)
  result['dependencies']={'E010_v0.3.1_outputs_sha256':e010_hash,
                          'E011_v0.3.0_outputs_sha256':e011.parent_zip_sha256,
                          'E011_seed_contract_schema':e011.schema['schema'],
                          'seed_identity':{k:seed[k] for k in ('topology_id','provider_group','carrier_id','static_seed_id','seed_role','evidence_class')},
                          'source':source,'E011_capabilities':seed['capabilities'],
                          'E011_literature_gates':seed['literature_gate_status']}
  # `DYNAMICS_READY` requires all three original source gates and source integrity.
  result['implementation']={'extension_version':'0.3.2','sha256':sha256_file(Path(__file__).parent/'pklsa_builder'/'dynamics_ready.py')}
  result['dynamic_gate_ledger']={
   'DYN0_SOURCE_AUTHENTICITY':{'status':'PASS','execution_status':'EXECUTED','reason':'E011 primary source + exact raw SHA256 verified'},
   'DYN1_FINITE_CORE_RESOLUTION':{'status':'PASS' if result['checks']['core_resolution'] else 'FAIL','execution_status':'EXECUTED'},
   'DYN2_SPATIAL_CONVERGENCE':{'status':'PASS' if result['checks']['spatial_velocity_convergence'] else 'FAIL','execution_status':'EXECUTED'},
   'DYN3_RK4_TEMPORAL_CONVERGENCE':{'status':'PASS' if result['checks']['temporal_RK4_convergence'] else 'FAIL','execution_status':'EXECUTED'},
   'DYN4_ENERGY_LENGTH_CLEARANCE':{'status':'PASS' if all(result['checks'][g] for g in ('energy_proxy_diagnostic','filament_length_diagnostic','nonlocal_clearance_proxy')) else 'FAIL','execution_status':'EXECUTED'},
   'DYN5_FILAMENT_NUMERICAL_READINESS':{'status':'PASS' if result['status']=='DYNAMICS_READY' else 'FAIL','execution_status':'EXECUTED','qualification':result['scientific_authority']},
   'DYN6_FULL_3D_EULER':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED','reason':'full Euler PDE solver and independent physical convergence not supplied'},
   'DYN7_INTRINSIC_SWIRL_CLOCK':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED','reason':'no independent eigenfrequency observable'},
  }
  result['independence_note']='One selected upstream seed: no cross-provider dynamic replication established.' 
  result['full_3D_Euler_status']='UNRESOLVED'
  result['A069_GP_comparison']='NOT_RUN'
  canonical_json_file(out,result)
  print(json.dumps({'output':str(out),'status':result['status'],
                    'model':MODEL_ID,'checks':result['checks']},indent=2))
  return 0 if result['status']=='DYNAMICS_READY' else 2
 except Exception as exc:
  # fail-closed, no fake PASS output / no overwrite
  print(f'REJECTED: {type(exc).__name__}: {exc}',file=sys.stderr)
  return 3
if __name__=='__main__':raise SystemExit(main())
