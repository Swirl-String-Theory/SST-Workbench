#!/usr/bin/env python3
"""Read-only A003 v0.2.5 exact torus braid-reference audit (not geometry certification)."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from fourier_atlas_adapter import resolve_atlas_root, validate_atlas, atomic_json
from g5_extended import analytic_braid_screen, TORUS_FAMILIES


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas',type=Path,default=None)
    p.add_argument('--out',type=Path,default=Path('outputs_g5c_braid_reference'))
    args=p.parse_args(argv)
    root=resolve_atlas_root(args.atlas)
    registry,report=validate_atlas(root)
    selected={}
    for record in registry['records']:
        if record['family'] in TORUS_FAMILIES:
            selected.setdefault(record['id'],record)
    results=[{'id':ident,**analytic_braid_screen(rec)} for ident,rec in sorted(selected.items())]
    all_ok=bool(results) and all(rec['status']=='PASS_BRAID_REFERENCE_ONLY' for rec in results)
    out={'schema':'sst.a003.g5c.braid-reference/1',
         'adapter_version':'0.2.8.1','atlas_manifest_sha256':registry['atlas_manifest_sha256'],
         'status':'PASS_BRAID_REFERENCE_ONLY' if all_ok else 'FAIL_BRAID_ALGEBRA',
         'checked_analytic_torus_seeds':len(results),
         'validated_source_xyz_count':report['source_records'],
         'source_byte_changes':False, 'knot_topology_certified':False,
         'chirality_certified':False,'pklsa_euler_run':False,
         'scientific_limit':'Burau and torus polynomial references both use declared p,q, not independent space-curve invariants.',
         'seed_results':results}
    atomic_json(args.out/'g5c_braid_reference.json',out)
    print(json.dumps({'status':out['status'],
                      'checked_analytic_torus_seeds':len(results),
                      'validated_source_xyz_count':report['source_records'],
                      'knot_topology_certified':False},indent=2))
    return 0 if all_ok else 2

if __name__=='__main__':
    raise SystemExit(main())
