from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from run_panel import canonical_entries
from sst_blind.multitopology import load_multicurve, linking_matrix, normalize_components, build_generic_modes

def main():
    entries=canonical_entries()
    need={'knot_0.1','link_2.2.1','torus_6.9'}
    got={e['source']:e for e in entries if e['source'] in need}
    assert set(got)==need
    c,m=load_multicurve(got['link_2.2.1']['path'],'knotplot',got['link_2.2.1']['metrics_path'])
    assert len(c)==2
    lk=linking_matrix(c)[0,1]
    assert abs(abs(lk)-1)<0.01,lk
    c,m=load_multicurve(got['torus_6.9']['path'],'knotplot',got['torus_6.9']['metrics_path'])
    assert len(c)==3
    A=linking_matrix(c)
    vals=[abs(A[i,j]) for i in range(3) for j in range(i+1,3)]
    assert all(abs(z-6)<0.02 for z in vals),vals
    c,_=normalize_components(c,n_total=72)
    mi=build_generic_modes(c,kelvin_harmonics=(2,))
    assert len(mi['modes'])>=15
    print({'ok':True,'hopf_Lk':lk,'torus_6_9_pairwise_Lk':vals,'generic_mode_count':len(mi['modes'])})
    return 0
if __name__=='__main__':raise SystemExit(main())
