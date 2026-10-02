import csv,json
from pathlib import Path
import numpy as np
from sst_qhp_falsifier.prepare import prepare
from sst_qhp_falsifier.geometry import radius_gyration


def _circle(path,r,n=64):
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    x=np.c_[r*np.cos(t),r*np.sin(t),np.zeros_like(t)]
    np.savetxt(path,x)


def test_family_anchor_scale_preserves_relative_breathing(tmp_path):
    root=tmp_path/'qhp'; root.mkdir()
    rows=[]
    for q,r in [(-0.1,0.9),(0.0,1.0),(0.1,1.1)]:
        name=f'x_{q:+.1f}.txt'.replace('+','p').replace('-','m')
        _circle(root/name,r)
        rows.append({'file':name,'family':'knot_test','q':q,'h':0.0,'p':0.0,'replicate':'0','geometry_ok':'true'})
    mp=root/'qhp_metadata.csv'
    with mp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    out=tmp_path/'prepared'
    cfg={'n_points':48,'blind_seed':1,'normalize_geometry_scale':True,'scale_normalization_mode':'family_anchor'}
    s=prepare(root,out,cfg,mp)
    assert s['scale_normalization_mode']=='family_anchor'
    with (out/'blind_catalog.csv').open(newline='',encoding='utf-8') as f:
        cat=list(csv.DictReader(f))
    z=np.load(out/'blind_geometries.npz')
    byq={float(r['q']):radius_gyration(z[r['candidate_id']]) for r in cat}
    assert abs(byq[0.0]-1.0)<1e-10
    assert abs(byq[-0.1]-0.9)<2e-3
    assert abs(byq[0.1]-1.1)<2e-3
