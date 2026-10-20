#!/usr/bin/env python3
"""Read-only inventory of original KnotPlot plaintext exports.

Blank lines separate components. All imported old relaxations are quarantined;
measurements are not topology, thickness, or physics certifications.
"""
import argparse,csv,hashlib,math
from pathlib import Path
import numpy as np

def components(text):
    ans=[];c=[]
    for line in text.splitlines()+['']:
        if not line.strip():
            if c:ans.append(np.array(c,dtype=np.float64));c=[]
            continue
        if line.lstrip().startswith('#'): continue
        a=line.split()
        if len(a)!=3:raise ValueError('Non-XYZ line, no silent component guessing')
        p=[float(v) for v in a]
        if not all(math.isfinite(v) for v in p):raise ValueError('nonfinite')
        c.append(p)
    return ans

def run():
    ar=argparse.ArgumentParser()
    ar.add_argument('directory',type=Path)
    ar.add_argument('--csv',type=Path,default=Path('legacy_quarantine_inventory.csv'))
    args=ar.parse_args();seen={};rows=[]
    for path in sorted(args.directory.rglob('*.txt')):
        raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        try:
            pp=components(raw.decode('utf-8-sig'))
            if not pp or any(len(p)<4 for p in pp):raise ValueError('invalid component')
            lens=[];cvs=[]
            for p in pp:
                e=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
                if np.min(e)<=0:raise ValueError('zero-length edge')
                lens.append(float(np.sum(e)));cvs.append(float(np.std(e)/np.mean(e)))
            status='QUARANTINE_HISTORICAL_ONLY'
            err=''
        except Exception as exc:
            pp=[];lens=[];cvs=[];status='UNPARSEABLE';err=str(exc)
        rows.append(dict(file=str(path.resolve()),raw_sha256=sha,byte_duplicate_of=seen.get(sha,''),
                         components=len(pp),n_by_component=';'.join(str(len(p)) for p in pp),
                         L_by_component=';'.join(f'{v:.15g}' for v in lens),
                         edge_CV_by_component=';'.join(f'{v:.15g}' for v in cvs),
                         status=status,error=err))
        seen.setdefault(sha,str(path.resolve()))
    args.csv.parent.mkdir(parents=True,exist_ok=True)
    with args.csv.open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=list(rows[0]) if rows else ['file','status']);w.writeheader();w.writerows(rows)
    print(f'{len(rows)} files inventoried; 0 promoted to physics')
if __name__=='__main__':run()

