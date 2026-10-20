#!/usr/bin/env python3
"""Independent structural and SHA verification of SST historical XYZ bundles."""
from __future__ import annotations
import argparse,hashlib,io,json
from pathlib import Path
import numpy as np

def verify_directory(directory:Path):
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    resolutions=manifest['resolutions']
    declared={}
    for name,row in manifest['seeds'].items():
        for file,attrs in row['files'].items():declared[file]=attrs
    actual={p.name for p in directory.iterdir() if p.suffix.lower()=='.xyz'}
    issues=[]
    if actual!=set(declared):issues.append('Orphan/missing XYZ filenames: '+repr(sorted(actual^set(declared))))
    expected_n=2*4*len(set(resolutions))
    if len(actual)!=expected_n:issues.append(f'Expected {expected_n} XYZ, found {len(actual)}')
    for fn,attrs in declared.items():
        p=directory/fn
        if not p.exists():continue
        if hashlib.sha256(p.read_bytes()).hexdigest()!=attrs['sha256']:issues.append('SHA mismatch '+fn)
        try:xyz=np.loadtxt(io.BytesIO(p.read_bytes()))
        except Exception as exc:issues.append(f'parse {fn} {exc}');continue
        n=int(attrs['N'])
        if xyz.shape!=(n,3) or not np.isfinite(xyz).all():issues.append('shape/finite '+fn);continue
        if np.linalg.norm(xyz[0]-xyz[-1])<1e-12:issues.append('duplicate endpoint '+fn)
        edges=np.linalg.norm(xyz-np.roll(xyz,1,axis=0),axis=1)
        if not np.min(edges)>0 or (edges.std()/edges.mean())>1e-3:issues.append('unequal edges '+fn)
    if manifest['version'] not in ('0.2.2','0.2.1'):issues.append('unknown version')
    check=directory/'SHA256SUMS.txt'
    if check.exists():
        for line in check.read_text(encoding='utf-8').splitlines():
            digest, name=line.split('  ',1)
            path=directory/name
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:issues.append('SHA256SUMS bad: '+name)
    for seed in manifest['seeds']:
        for n in resolutions:
            def load(label):return np.loadtxt(directory/f'{seed}_{label}_N{n}_arclength.xyz')
            try:
                a,b,c,d=(load(k) for k in ('orig_ccw','orig_cw','mirrorX_ccw','mirrorX_cw'))
                if not np.array_equal(a[0],b[0]) or not np.array_equal(b[1:],a[:0:-1]):issues.append('wrong reverse '+seed+str(n))
                if not np.array_equal(c[:,0],-a[:,0]) or not np.array_equal(c[:,1:],a[:,1:]):issues.append('wrong mirror '+seed+str(n))
                if not np.array_equal(d[1:],c[:0:-1]):issues.append('wrong mirror-reverse '+seed+str(n))
            except Exception as exc:issues.append('variant check '+seed+str(n)+' '+str(exc))
    return {'ok':not issues,'count':len(actual),'expected':expected_n,'resolutions':resolutions,'issues':issues}

def main():
    p=argparse.ArgumentParser();p.add_argument('--dir',type=Path,required=True);args=p.parse_args()
    r=verify_directory(args.dir)
    print(json.dumps(r,indent=2))
    if not r['ok']:raise SystemExit(2)
if __name__=='__main__':main()
