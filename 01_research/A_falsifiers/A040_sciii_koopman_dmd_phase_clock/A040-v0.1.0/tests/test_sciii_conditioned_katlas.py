import json
from pathlib import Path
import numpy as np
from sst_modal_clock.sources import discover_katlas


def test_conditioned_katlas_geometry_is_preferred(tmp_path: Path):
    d=tmp_path/'links'/'02'/'L2a1'; d.mkdir(parents=True)
    obj={'identity':{'katlas_id':'L2a1','kind':'link','crossings':2,'table':'Thistlethwaite'},'presentations':{'pd':['X<sub>4132</sub> X<sub>2314</sub>'],'gauss':['{1, -2}, {2, -1}'],'dt':['']},'invariants':{}}
    (d/'katlas.json').write_text(json.dumps(obj))
    t=np.linspace(0,2*np.pi,64,endpoint=False)
    a=np.c_[np.cos(t),np.sin(t),np.zeros_like(t)]
    b=np.c_[.5+np.cos(t),np.zeros_like(t),np.sin(t)]
    pts=np.vstack([a,b]); np.savez_compressed(d/'conditioned_geometry.npz',points=pts,component_offsets=np.array([0,64,128],dtype=np.int64))
    rows,st=discover_katlas(tmp_path,64)
    assert len(rows)==1
    assert st['conditioned_link_records']==1
    assert rows[0].metadata['geometry_origin']=='generated_from_katlas_pd_conditioned'
    assert rows[0].metadata['translator']=='SST-KATLAS-ISOTOPY-HARMONIC-2.0'
