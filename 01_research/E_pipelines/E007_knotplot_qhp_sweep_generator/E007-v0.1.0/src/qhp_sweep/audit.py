from __future__ import annotations
import csv,json,sys,collections
from pathlib import Path


def main():
    root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('../../KnotPlot/qhp')
    meta=root/'qhp_metadata.csv'
    if not meta.exists(): raise SystemExit(f'Missing {meta}')
    rows=list(csv.DictReader(meta.open(encoding='utf-8')))
    if not rows: raise SystemExit('qhp_metadata.csv is empty')
    bad=[r for r in rows if r.get('geometry_ok','').lower()!='true']
    fam=sorted(set(r['family'] for r in rows))
    files=[r['file'] for r in rows]
    counts=collections.Counter(files)
    duplicate_paths=sorted(k for k,v in counts.items() if v>1)
    missing=sorted(f for f in set(files) if not (root/f).is_file())
    fam_seed=collections.defaultdict(set)
    for r in rows: fam_seed[r['family']].add(r.get('seed_sha256',''))
    mixed_families=sorted(k for k,v in fam_seed.items() if len(v)>1)
    actual_txt=sum(1 for p in root.rglob('*.txt') if p.is_file())
    passed=(not duplicate_paths and not missing and not mixed_families and len(set(files))==len(rows))
    result={
        'n_rows':len(rows),'n_unique_output_paths':len(set(files)),'n_actual_txt_files':actual_txt,
        'families':fam,'n_families':len(fam),'n_geometry_rejected':len(bad),
        'duplicate_output_paths':duplicate_paths[:20],'n_duplicate_output_paths':len(duplicate_paths),
        'missing_output_files':missing[:20],'n_missing_output_files':len(missing),
        'mixed_seed_families':mixed_families,'pass':passed,
    }
    print(json.dumps(result,indent=2))
    if not passed: raise SystemExit(2)

if __name__=='__main__': main()
