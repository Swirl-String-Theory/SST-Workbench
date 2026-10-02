from __future__ import annotations
import argparse, json, re
from pathlib import Path

def count_vertices(path: Path):
    n=0
    for line in path.read_text(encoding='utf-8',errors='ignore').splitlines():
        s=line.strip()
        if not s or s.startswith('#'): continue
        parts=s.replace(',',' ').split()
        if len(parts)>=3:
            try: float(parts[0]); float(parts[1]); float(parts[2]); n+=1
            except ValueError: pass
    return n

def group_name(stem: str):
    m=re.match(r'((?:knot|link|torus)_[0-9.]+)',stem,re.I)
    return m.group(1) if m else stem.split('_trial_')[0].split('_rr_')[0]

def main():
    ap=argparse.ArgumentParser(description='Create a PRIVATE pre-blinding manifest from relaxed XYZ/TXT files.')
    ap.add_argument('root'); ap.add_argument('--glob',default='**/*polish*.txt'); ap.add_argument('--out',default='datasets.private.json'); ap.add_argument('--radius',type=float,default=0.5)
    args=ap.parse_args(); root=Path(args.root).resolve(); cases=[]
    for p in sorted(root.glob(args.glob)):
        name=p.name.lower(); uniform=('uniform' in name or 'resample' in name)
        cases.append({
            'path':str(p), 'label':p.name, 'group':group_name(p.stem), 'resolution':count_vertices(p),
            'radius':args.radius,
            'source_role':'vortexlab-uniform-downstream-resample' if uniform else 'ridgerunner-polish-audit-geometry',
            'geometry_status':'unknown-imported-relaxed', 'complete_mechanical_model':False
        })
    obj={'preregistration':{},'cases':cases}
    Path(args.out).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')
    print(f'Wrote {args.out} with {len(cases)} cases. Review radius, grouping, source_role and geometry_status before blinding.')
if __name__=='__main__': main()
