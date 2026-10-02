from __future__ import annotations
import argparse, json
from pathlib import Path
from .models import QualificationConfig
from .builder import build_release, archive_release
from .topology_db import ingest_legacy_database, write_database_bundle
from .doctor import doctor
from .repo_finder import scan_repository, write_scan_outputs, DEFAULT_CATALOG


def _default_source(name):
    return str(Path(__file__).resolve().parents[1]/'data'/'topology_sources'/name)


def main(argv=None):
    ap=argparse.ArgumentParser(prog='pklsa-v030-builder')
    sub=ap.add_subparsers(dest='cmd',required=True)

    d=sub.add_parser('doctor'); d.add_argument('--workbench-root'); d.add_argument('--base')

    s=sub.add_parser('scan-repo',help='Automatically locate and inventory all A001-A008 knot-source families in SST-Workbench')
    s.add_argument('--workbench-root',required=True)
    s.add_argument('--source-catalog',default=str(DEFAULT_CATALOG))
    s.add_argument('--out',required=True)
    s.add_argument('--deep-hash',action='store_true',help='SHA-256 every discovered source file; slower on multi-GB archives')
    s.add_argument('--search-depth',type=int,default=7)
    s.add_argument('--no-unregistered-search',action='store_true')

    p=sub.add_parser('profile-db'); p.add_argument('path'); p.add_argument('--kind',choices=['knot','link'],default='knot'); p.add_argument('--out',default='db_profile_out')

    b=sub.add_parser('build')
    b.add_argument('--base',required=True)
    b.add_argument('--workbench-root')
    b.add_argument('--source-catalog',default=str(DEFAULT_CATALOG))
    b.add_argument('--config',required=True)
    b.add_argument('--topology',action='append',default=[])
    b.add_argument('--out',required=True)
    b.add_argument('--knotinfo-xls',default=_default_source('knotinfo_data_complete.xls.zip'))
    b.add_argument('--linkinfo-xls',default=_default_source('linkinfo_data_complete.xls'))
    b.add_argument('--archive',action='store_true'); b.add_argument('--archive-dir')
    b.add_argument('--allow-source-gaps',action='store_true',help='Do not abort when A001-A008 coverage gate fails; diagnostic only')
    b.add_argument('--fail-on-unregistered',action='store_true',help='Publication guard: abort if strong unregistered source candidates are found')
    b.add_argument('--deep-source-hash',action='store_true')
    b.add_argument('--strict-topology-db',action='store_true',help='Abort unless bundled KnotInfo and LinkInfo databases ingest successfully')

    args=ap.parse_args(argv)
    if args.cmd=='doctor':
        print(json.dumps(doctor(args.workbench_root,args.base),indent=2)); return 0
    if args.cmd=='scan-repo':
        r=scan_repository(args.workbench_root,args.source_catalog,hash_files=args.deep_hash,search_depth=args.search_depth,find_unregistered=not args.no_unregistered_search)
        write_scan_outputs(r,args.out)
        print(json.dumps({'coverage_gate':r['coverage_gate'],'unregistered_count':len(r['unregistered_source_candidates']),'output':str(Path(args.out).resolve())},indent=2)); return 0 if r['coverage_gate']['pass'] else 3
    if args.cmd=='profile-db':
        r=ingest_legacy_database(args.path,args.kind); write_database_bundle(r,args.out,args.kind+'info'); print(json.dumps({'records':len(r['records']),'profiles':r['profiles']},indent=2)); return 0
    if args.cmd=='build':
        cfg=QualificationConfig.load(args.config); tops=args.topology or ['3_1']
        rel=build_release(
            base=args.base,output=args.out,config=cfg,workbench_root=args.workbench_root,
            knotinfo_xls=args.knotinfo_xls,linkinfo_xls=args.linkinfo_xls,topologies=tops,
            source_catalog=args.source_catalog,strict_source_coverage=not args.allow_source_gaps,
            fail_on_unregistered=args.fail_on_unregistered,deep_source_hash=args.deep_source_hash,strict_topology_db=args.strict_topology_db)
        if args.archive:
            z,sha=archive_release(args.out,args.archive_dir); rel['archive']=str(z); rel['archive_sha256']=sha
        print(json.dumps(rel,indent=2)); return 0
    return 2

if __name__=='__main__': raise SystemExit(main())
