import numpy as np
from pathlib import Path
from sst_finite_core_falsifier.profiles import profile,vorticity_components
from sst_finite_core_falsifier.geometry import torus_knot,resample_closed,arclength,bishop_holonomy,carrier_catalog

def test_finite_core_profiles_are_regular_and_helical():
    r=np.linspace(0,5,201)
    for name in ('gaussian','smooth_rankine','compact_poly'):
        U,V=profile(name,r,0.8)
        assert np.all(np.isfinite(U)) and np.all(np.isfinite(V))
        assert abs(V[0])<1e-12
        oa,ot=vorticity_components(r,U,V)
        assert np.sqrt(np.mean(oa[:40]**2))>1e-3
        assert np.sqrt(np.mean(ot[:40]**2))>1e-3

def test_closed_geometry_and_holonomy_are_finite():
    c=resample_closed(torus_knot(2,3,1000),384)
    assert arclength(c)>1
    h=bishop_holonomy(c)
    assert np.isfinite(h) and -np.pi<=h<=np.pi

def test_catalog_contains_torus_twist_and_gear():
    root=Path(__file__).parents[1]/'assets'/'fseries'; cats=carrier_catalog(root,192)
    assert 'TORUS_T2_3' in cats and 'TWIST_5_2' in cats and 'TRIPLE_GEAR_T3_3' in cats
    assert cats['TWIST_5_2'].get('source_qualified',False)
