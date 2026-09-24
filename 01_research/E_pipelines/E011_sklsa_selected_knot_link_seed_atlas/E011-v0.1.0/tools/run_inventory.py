from __future__ import annotations
import argparse, json, sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from sklsa.selection import load_selection, selected_ids
from sklsa.discovery import scan_knotplot


def normalize_workbench_root(value: str | Path) -> Path:
    """Accept the Workbench itself, its parent, or a descendant and recover the canonical root."""
    p=Path(value).absolute()
    probes=[p]
    probes.extend(p.parents)
    child=p/'SST-Workbench'
    if child not in probes:
        probes.insert(1,child)
    for q in probes:
        try:
            if q.name.lower()=='sst-workbench' and (q/'01_research').is_dir() and ((q/'03_data').exists() or (q/'02_libraries').exists()):
                return q
        except OSError:
            continue
    raise RuntimeError(f'could not resolve SST-Workbench root from: {p}')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--workbench-root',required=True)
    ap.add_argument('--mode',choices=['poc','core','selected'],default='poc')
    ap.add_argument('--include-sentinels',action='store_true')
    ap.add_argument('--output-root')
    args=ap.parse_args()
    root=normalize_workbench_root(args.workbench_root)
    print(f'[root] canonical Workbench: {root}')
    cfg=load_selection(HERE/'configs'/'selected_topologies.json')
    if args.mode=='poc': wanted=cfg['poc']
    elif args.mode=='core': wanted=cfg['core_knots']
    else: wanted=selected_ids(cfg,include_sentinels=args.include_sentinels)
    wanted=list(dict.fromkeys(wanted)); selected=set(wanted)
    diagnostics=[]
    recs=scan_knotplot(root,selected,diagnostics=diagnostics)
    out=Path(args.output_root) if args.output_root else HERE/'E011_SKLSA_KnotPlot_Selected_v0.1.0-outputs'
    out.mkdir(parents=True,exist_ok=True)
    (out/'KNOTPLOT_CARRIERS.json').write_text(json.dumps(recs,indent=2),encoding='utf-8')
    (out/'DISCOVERY_DIAGNOSTICS.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf-8')
    by=defaultdict(list)
    for r in recs: by[r['topology_id']].append(r)
    rows=[]
    for t in wanted:
        cs=by.get(t,[])
        rows.append({'topology_id':t,'carrier_count':len(cs),'status':'DISCOVERED' if cs else 'MISSING_KNOTPLOT_CARRIER'})
    (out/'TOPOLOGY_SOURCE_MATRIX.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    summary={
      'schema':'E011-SKLSA-KNOTPLOT-INVENTORY-2',
      'created_utc':datetime.now(timezone.utc).isoformat(),
      'workbench_root':str(root),
      'mode':args.mode,
      'selected_topology_count':len(wanted),
      'topologies_with_knotplot_carrier':sum(1 for r in rows if r['carrier_count']>0),
      'topologies_missing_knotplot_carrier':sum(1 for r in rows if r['carrier_count']==0),
      'carrier_count':len(recs),
      'suffix_counts':dict(sorted(Counter(r['suffix'] for r in recs).items())),
      'discovery_warning_count':len(diagnostics),
      'gate':'PASS_INVENTORY_ONLY' if recs else 'FAIL_NO_SELECTED_KNOTPLOT_CARRIERS',
      'scientific_boundary':'Inventory/discovery only. No seed-quality, dynamics, or SST particle claim.'
    }
    (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))
    return 0 if recs else 2

if __name__=='__main__': raise SystemExit(main())
