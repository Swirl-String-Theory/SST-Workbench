#!/usr/bin/env python3
"""Independent admission check of shipped Ruban T(2,3) analytic XYZ files."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def main():
    a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path(__file__).resolve().parent);o=a.parse_args()
    root=o.root
    mf=json.loads((root/'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    assert mf['exact_parameters']['B0']=='0.154'
    assert mf['exact_parameters']['delta']=='0.05'
    for entry in mf['files']:
        f=root/'seeds'/entry['filename'];assert f.is_file(),f
        assert hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256'],f
        xyz=np.loadtxt(f,comments='#',usecols=(0,1,2))
        assert xyz.shape==(entry['n_vertices'],3)
        assert np.isfinite(xyz).all()
        rxy=np.hypot(xyz[:,0],xyz[:,1]);r=np.hypot(rxy-1.0,xyz[:,2])
        assert max(abs(r-.154))<1e-12
        wind_tor=round(np.unwrap(np.arctan2(xyz[:,1],xyz[:,0]))[-1]/(2*np.pi))
        wind_pol=round(np.unwrap(np.arctan2(xyz[:,2],rxy-1))[-1]/(2*np.pi))
        assert (wind_tor,wind_pol)==(2,3),(wind_tor,wind_pol)
        segments=np.linalg.norm(np.roll(xyz,-1,axis=0)-xyz,axis=1)
        if entry['sampling']=='equal_arclength':assert segments.max()/segments.min()<1.00001
        else:assert segments.max()/segments.min()<1.4
        print(f"PASS {f.name}: SHA256, N={len(xyz)}, winding=(2,3), r0=0.154, seg_ratio={segments.max()/segments.min():.9f}")
    print('ALL_SEEDS_VERIFIED: MATHEMATICAL_CANDIDATE; Ruban dynamics NOT tested')

if __name__=='__main__':main()
