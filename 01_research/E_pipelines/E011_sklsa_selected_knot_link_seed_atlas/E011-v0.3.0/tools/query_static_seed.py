from __future__ import annotations
import argparse,json
from pathlib import Path


def load_jsonl(path: Path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def main():
    ap=argparse.ArgumentParser(description='Query E011-v0.3.0 STATIC_READY provider anchors for a falsifier')
    ap.add_argument('--atlas-output',required=True)
    ap.add_argument('--topology',required=True)
    ap.add_argument('--capability',action='append',default=[])
    ap.add_argument('--all-primary',action='store_true',help='Return all primary STATIC_READY carrier variants instead of provider anchors')
    args=ap.parse_args()
    root=Path(args.atlas_output)
    fn='STATIC_READY_PRIMARY_SEEDS.jsonl' if args.all_primary else 'STATIC_READY_PROVIDER_ANCHORS.jsonl'
    rows=load_jsonl(root/fn)
    rows=[r for r in rows if r.get('topology_id')==args.topology]
    rows=[r for r in rows if all((r.get('capabilities') or {}).get(c) is True for c in args.capability)]
    idx=json.loads((root/'STATIC_READY_INDEX.json').read_text(encoding='utf-8'))
    status=next((r for r in idx if r.get('topology_id')==args.topology),None)
    print(json.dumps({'topology':status,'requested_capabilities':args.capability,'result_count':len(rows),'seeds':rows},indent=2))
    return 0 if rows else 3

if __name__=='__main__': raise SystemExit(main())
