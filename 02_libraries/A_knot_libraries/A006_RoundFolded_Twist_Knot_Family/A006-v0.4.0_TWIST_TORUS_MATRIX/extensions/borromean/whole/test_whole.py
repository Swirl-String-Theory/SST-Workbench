#!/usr/bin/env python3
import argparse,sys,math,json,tempfile
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from build_whole import load_xyz,write_xyz,transport,clearance,gauss,CFG,KNOTS,PAIR,sha,ref_lookup,closed_resample,edge_metrics,allocate_counts,allocate_from_smallest,closed_resample_best_phase
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
    # Periodic reference seam regression (the actual v0.4.2a bug).
    g=load_xyz(HERE/'references'/'borromean_balanced.txt')[0]
    wrap,c,*_=ref_lookup(g,np.array([-1.e-5,1.e-5,2*np.pi-1.e-5,2*np.pi+1.e-5]))
    assert np.linalg.norm(wrap[0]-wrap[2])<1.e-8
    assert np.linalg.norm(wrap[1]-wrap[3])<1.e-8
    assert np.linalg.norm(wrap[0]-wrap[1])<.01
    print('PASS: reference angular interpolation is periodic at 0/2pi')
    theta=np.arange(64)*2*np.pi/64
    ring=np.column_stack((np.cos(theta),np.sin(theta),np.zeros(64)))
    out=closed_resample(ring,257)
    m=edge_metrics(out)
    assert len(out)==257 and .99<m['closure_over_median']<1.01
    assert .98<m['min_over_median'] and m['max_over_median']<1.02
    print('PASS: implicit cyclic closure and equal arc spacing')
    assert allocate_counts([2.,2.,4.],total=1000)==(250,250,500)
    assert allocate_counts([2.,2.,4.],explicit=(1024,1024,1165))==(1024,1024,1165)
    print('PASS: total-count and explicit per-component bead allocation')
    assert allocate_from_smallest([10,15,12.5],256)==(256,384,320)
    assert allocate_from_smallest([20,20,23],1024)==(1024,1024,1178)
    try: allocate_from_smallest([1,0,1],256)
    except ValueError: pass
    else: raise AssertionError('Zero-length component accepted')
    print('PASS: MIN 256/512/1024 budget scales from shortest final length')
    ring2=np.column_stack((np.cos(theta),np.sin(theta),np.zeros(64)))
    resampled,offset=closed_resample_best_phase(ring2,256)
    assert len(resampled)==256 and 0<=offset<1 and edge_metrics(resampled)['min_over_median']>.99
    print('PASS: best-phase cyclic resampling and seam uniformity')
    from strict_xyz import assert_strict_xyz
    with tempfile.TemporaryDirectory() as td:
        fn=Path(td)/'mixed.xyz'
        comps=[ring[:48],ring[:56],ring]
        write_xyz(fn,comps)
        assert assert_strict_xyz(fn,(48,56,64))==[48,56,64]
        assert fn.read_text().count('\n\n')==2
    print('PASS: unequal bead counts in single headerless 3-block XYZ')
    print('UNCERTIFIED: Milnor mu123, component Alexander after transport, KnotPlot ago and Euler/PKLSA')

if __name__=='__main__':main()
