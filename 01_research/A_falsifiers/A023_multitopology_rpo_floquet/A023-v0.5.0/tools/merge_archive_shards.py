from __future__ import annotations
import argparse,csv,json
from pathlib import Path
from collections import Counter

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('parent'); a=ap.parse_args(); root=Path(a.parent)
    shards=sorted([p for p in root.glob('shard_*') if p.is_dir()]); rows=[]; gates=[]; archive=[]
    for s in shards:
        q=s/'summary_metrics.csv'
        if q.exists():
            with q.open(encoding='utf-8',newline='') as f: rows.extend(list(csv.DictReader(f)))
        g=s/'GATE_CONCLUSIONS.md'
        if g.exists(): gates.append(f'\n\n# {s.name}\n\n'+g.read_text(encoding='utf-8'))
        c=s/'ARCHIVE_CONCLUSIONS.md'
        if c.exists(): archive.append(f'\n\n# {s.name}\n\n'+c.read_text(encoding='utf-8'))
    if rows:
        fields=[]
        for r in rows:
            for k in r:
                if k not in fields: fields.append(k)
        with (root/'MERGED_summary_metrics.csv').open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    if gates: (root/'MERGED_GATE_CONCLUSIONS.md').write_text(''.join(gates),encoding='utf-8')
    if archive: (root/'MERGED_ARCHIVE_CONCLUSIONS_BY_SHARD.md').write_text(''.join(archive),encoding='utf-8')
    cnt=Counter(r.get('status','?') for r in rows); cls=Counter(r.get('topology_class','?') for r in rows)
    lines=['# Merged Full-Archive Summary','',f'Shards found: **{len(shards)}**',f'Datasets merged: **{len(rows)}**','',f"PASS: **{cnt.get('PASS',0)}**, FAIL: **{cnt.get('FAIL',0)}**",'', '## Topology classes','', '| class | N |','|---|---:|']
    for k,v in sorted(cls.items()): lines.append(f'| {k} | {v} |')
    (root/'MERGED_ARCHIVE_SUMMARY.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'shards':len(shards),'datasets':len(rows),'status_counts':dict(cnt)},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
