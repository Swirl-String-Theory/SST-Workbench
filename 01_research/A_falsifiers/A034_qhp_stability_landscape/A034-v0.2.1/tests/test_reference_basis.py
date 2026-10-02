import csv,json
from pathlib import Path
import numpy as np
import sst_qhp_falsifier.run as runmod


def test_reference_basis_gives_all_components_on_star_grid(tmp_path,monkeypatch):
    prep=tmp_path/'prep'; prep.mkdir(); out=tmp_path/'out'
    n=32; t=np.linspace(0,2*np.pi,n,endpoint=False)
    x0=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    bq=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    bh=np.c_[np.zeros_like(t),np.zeros_like(t),np.cos(t)]
    bp=np.c_[np.zeros_like(t),np.zeros_like(t),np.sin(2*t)]
    specs=[(0,0,0),(-.1,0,0),(.1,0,0),(0,-.1,0),(0,.1,0),(0,0,-.1),(0,0,.1)]
    rows=[]; arrays={}
    for i,(q,h,p) in enumerate(specs):
        cid=f'C{i}'; arrays[cid]=x0+q*bq+h*bh+p*bp
        rows.append({'candidate_id':cid,'family_blind':'F','q':q,'h':h,'p':p,'replicate':'0'})
    with (prep/'blind_catalog.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
    np.savez_compressed(prep/'blind_geometries.npz',**arrays)

    def fake_velocity(x,gamma,core,ref,exp,req):
        # arbitrary normal-ish field; only finiteness and common basis matter here
        return 0.2*x, np.full(len(x),core)
    monkeypatch.setattr(runmod,'velocity_material',fake_velocity)
    monkeypatch.setattr(runmod,'rk4',lambda x,*args,**kwargs:x)
    monkeypatch.setattr(runmod,'backend_name',lambda:'test')
    runmod.run(prep,out,{'gamma_dimensionless':1.0,'core_fraction':0.04,'core_length_exponent':-0.5,
                         'require_native':False,'t_short':0.01,'dt_factor':0.01})
    with (out/'blind_qhp_field.csv').open(newline='',encoding='utf-8') as f:
        got=list(csv.DictReader(f))
    assert len(got)==7
    for r in got:
        assert r['has_tangent_q']=='True' and r['has_tangent_h']=='True' and r['has_tangent_p']=='True'
        assert np.isfinite(float(r['F_q']))
        assert np.isfinite(float(r['F_h']))
        assert np.isfinite(float(r['F_p']))
        assert float(r['basis_correlation_condition_number'])<100
