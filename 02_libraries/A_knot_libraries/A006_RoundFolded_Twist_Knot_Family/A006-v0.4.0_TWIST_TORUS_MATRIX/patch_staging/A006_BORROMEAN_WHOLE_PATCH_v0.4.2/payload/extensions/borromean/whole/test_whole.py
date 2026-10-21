#!/usr/bin/env python3
import argparse,sys,math,json,tempfile
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_whole import load_xyz,write_xyz,transport,clearance,gauss,CFG,KNOTS,PAIR,sha
sys.path.insert(0,str(HERE.parent))
from build_borromean import locate_seed

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);a=p.parse_args();root=a.root.resolve()
    assert (root/'SEED_MANIFEST.json').is_file()
    for k in ('5_2','6_1'):
        x,path=locate_seed(root,k,1024)
        assert x.shape==(1024,3) and np.isfinite(x).all()
    print('PASS: native v0.4.0 seed discovery and manifest hashes')
    for fn in ('borromean_flat.txt','borromean_balanced.txt'):
        g=load_xyz(HERE/'references'/fn)
        assert len(g)==3 and all(len(x)>30 for x in g)
    print('PASS: user provided FLAT/BALANCED 3-component XYZ parser')
    with tempfile.TemporaryDirectory() as td:
        arr=[np.array([[math.sin(j),math.cos(j),float(k)] for j in range(7)]) for k in range(3)]
        fn=Path(td)/'roundtrip.xyz'
        write_xyz(fn,arr)
        b=load_xyz(fn,7)
        assert all(np.allclose(x,y) for x,y in zip(arr,b))
        s=fn.read_text();assert s.count('\n\n')==2 and s.endswith('\n')
        assert not any(x.startswith(('Component','Comp','[')) for x in s.splitlines())
    print('PASS: one combined 3-component XYZ; 2 exact blank separators')
    assert all(x[0] in ('borromean_flat.txt','borromean_balanced.txt') for x in CFG.values())
    print('PASS: whole-component profile registry')
    print('UNCERTIFIED: Milnor mu123, component Alexander after transport, KnotPlot ago and Euler/PKLSA')

if __name__=='__main__':main()
