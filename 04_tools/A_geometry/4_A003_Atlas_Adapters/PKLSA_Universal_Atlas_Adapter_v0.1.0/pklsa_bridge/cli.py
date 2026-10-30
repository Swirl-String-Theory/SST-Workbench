"""Command-line tools for the E010 v0.4.0 universal dataset adapter."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from .adapter import AtlasBridge, AtlasContractError, AdmissionError, verify_export


def positive_int(s):
    n=int(s)
    if n < 1:raise argparse.ArgumentTypeError('Must be >=1')
    return n


def parser():
    p=argparse.ArgumentParser(
        prog='python -m pklsa_bridge.cli',
        description='E010 v0.4.0 -> immutable, explicit-consent falsifier dataset export')
    p.add_argument('--atlas',default=os.environ.get('E010_ATLAS'),
                   help='Extracted E010 v0.4.0 output folder OR its original portable .zip')
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('selftest',help='Run embedded regression tests (real atlas if --atlas provided)')
    sub.add_parser('verify-atlas',help='Verify pinned index and reader, no scientific claims')
    v=sub.add_parser('verify-dataset',help='Verify exported dataset checksums')
    v.add_argument('dataset_path')
    q=sub.add_parser('select',help='Query metadata only (default 20 displayed IDs)')
    e=sub.add_parser('export',help='Create-only dataset export with manifest and component XYZ')
    for x in (q,e):
        x.add_argument('--id',action='append',dest='ids',help='Exact record ID (repeatable)')
        x.add_argument('--topology',help='e.g. 3_1, 5_2; source label not proof')
        x.add_argument('--embedding',help='e.g. T_2_3, T_3_6')
        x.add_argument('--collection',choices=['historical_v031','ruban_v036'])
        x.add_argument('--variant',choices=['nominal','perturbed','historical'])
        x.add_argument('--provider')
        x.add_argument('--source-group',dest='independence_group')
        x.add_argument('--components',type=positive_int,dest='component_count')
        x.add_argument('--min-points',type=positive_int)
        x.add_argument('--b0-min',type=float)
        x.add_argument('--b0-max',type=float)
        x.add_argument('--historical-status',choices=['PASS','FAIL'])
        x.add_argument('--allow-research',action='store_true',
                       help='Explicit admission of research-only geometry for exploratory export; not physics admission')
        x.add_argument('--unique-geometry',action='store_true',
                       help='One ID per exact ordered float64 geometry hash (not topology dedup)')
    q.add_argument('--limit',type=positive_int,default=20)
    e.add_argument('--output',required=True)
    e.add_argument('--limit',type=positive_int,
                   help='Explicit truncate to at most N selection records')
    e.add_argument('--max-records',type=positive_int,default=100,
                   help='Safety maximum (default 100), not an implicit truncation')
    e.add_argument('--resample',type=positive_int,
                   help='Closed-polygon arclength interpolation (not source refinement)')
    e.add_argument('--scale',type=float,default=1.0,
                   help='Source coordinate multiplier; does NOT assign SI units')
    e.add_argument('--consumer',required=True,help='Consumer falsifier/version identifier')
    e.add_argument('--duplicate-policy',choices=['preserve','reject'],default='preserve')
    return p


def main(argv=None):
    if argv is None:
        argv=sys.argv[1:]
    aliases={'SELFTEST':'selftest','VERIFY':'verify-atlas','VERIFY_ATLAS':'verify-atlas',
             'SELECT':'select','EXPORT':'export','VERIFY_DATASET':'verify-dataset'}
    argv=[aliases.get(a,a) for a in argv]
    args=parser().parse_args(argv)
    if args.command=='verify-dataset':
        print(json.dumps(verify_export(args.dataset_path),indent=2))
        return 0
    if args.command=='selftest':
        env=os.environ.copy()
        if args.atlas:env['PKLSA_TEST_ATLAS']=str(Path(args.atlas).resolve())
        return subprocess.call([sys.executable,'-m','unittest','discover','-s','tests','-v'],
                               cwd=Path(__file__).resolve().parents[1],env=env)
    if not args.atlas:raise AtlasContractError('Supply --atlas or E010_ATLAS')
    with AtlasBridge(args.atlas) as atlas:
        if args.command=='verify-atlas':
            print(json.dumps({'status':'PASS_PINNED_INDEX_AND_ORIGINAL_READER',
                              'record_count':len(atlas.records),
                              'index_sha256':atlas.index_sha,
                              'scientific':'NOT_RUN'},indent=2));return 0
        conditions={k:getattr(args,k) for k in (
            'ids','topology','embedding','collection','variant','provider',
            'independence_group','component_count','min_points','b0_min','b0_max',
            'historical_status','allow_research','unique_geometry')}
        if args.command=='export':
            has_filter=any(v is not None for k,v in conditions.items() if k not in ('allow_research','unique_geometry'))
            if not has_filter:
                raise AdmissionError('Export requires at least one explicit record selection filter')
        ids=atlas.query(**conditions,limit=args.limit)
        if args.command=='select':
            print(json.dumps({'record_count_selected_or_limited':len(ids),'ids':ids,
                              'limit':args.limit,'scientific_admission':'NOT_GRANTED'},indent=2))
        else:
            if not ids:raise AdmissionError('No matching records')
            manifest=atlas.export_dataset(ids,args.output,allow_research=args.allow_research,
                                          resample_points=args.resample,scale=args.scale,
                                          consumer=args.consumer,max_records=args.max_records,
                                          duplicate_policy=args.duplicate_policy)
            print(json.dumps({'status':'EXPORTED_RESEARCH_DATASET_NOT_PHYSICS_ADMISSION',
                              'manifest':str(manifest), 'selected_records':len(ids),
                              'verification':verify_export(manifest.parent)},indent=2))
    return 0


if __name__=='__main__':
    try:raise SystemExit(main())
    except (AtlasContractError,ValueError,KeyError,FileNotFoundError) as exc:
        print(f'REFUSED: {exc}',file=sys.stderr)
        raise SystemExit(2)
