import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from near_unknot import annulus_squeeze,params,winding_number_xy,area_vector,PROFILES
from tikz_roundfold import dense_xyz,resample3
from build import recheck_topology

def test_radial_map_inverse():
    for k in ('5_2','6_1'):
        x,_=dense_xyz(k,density=75);c,R,_=params(x)
        q=annulus_squeeze(x,.2,1.0,c,R)
        r=np.linalg.norm(q[:,:2]-c,axis=1)
        x2=q.copy();x2[:,:2]=c+(q[:,:2]-c)*((R+(r-R)/.2)/r)[:,None]
        assert np.allclose(x,x2,rtol=1e-12,atol=1e-12)

def test_projected_winding():
    for k in ('5_2','6_1'):
        x,_=dense_xyz(k,density=40)
        c,R,_=params(x)
        assert winding_number_xy(x,c)==0
        for a in (.12,.23,.42):
            y=annulus_squeeze(x,a,2,c,R)
            assert winding_number_xy(y,c*2)==0

def test_crossing_and_poly_survive_squeeze():
    for k in ('5_2','6_1'):
        x,_=dense_xyz(k,density=120)
        c,R,_=params(x)
        for alpha in (.12,.42):
            p=resample3(annulus_squeeze(x,alpha,2,c,R),256)*12
            report=recheck_topology(p,k)
            assert report['alternating_lift_verified']

def test_toroidal_area_not_unknot():
    for k in ('5_2','6_1'):
        x,_=dense_xyz(k,density=75)
        c,R,_=params(x)
        q=annulus_squeeze(x,.12,1.0,c,R)
        area=area_vector(q)
        assert abs(area[2])/(np.pi*R*R)<.05

def test_invalid_profile_params():
    x,_=dense_xyz('5_2',density=30)
    for a in [-1,0,1.1]:
        try:annulus_squeeze(x,a,1)
        except ValueError:pass
        else:raise AssertionError('invalid parameter accepted')
