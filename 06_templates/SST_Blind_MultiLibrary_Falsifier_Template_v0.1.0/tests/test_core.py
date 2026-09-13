import numpy as np
from sst_falsifier_core.stats import nearest_rational,benjamini_hochberg
from sst_falsifier_core.geometry import uniform_resample_closed,segments
from sst_falsifier_core.backends import velocity

def test_rational_generic():
 r=nearest_rational(0.401,10); assert r["q"]<=10

def test_geometry_backend():
 t=np.linspace(0,2*np.pi,32,endpoint=False); p=np.c_[np.cos(t),np.sin(t),0*t]
 q=uniform_resample_closed(p,48); targets,mids,dls,tans,offs=segments([q]); v,b=velocity(targets,mids,dls,1,.05,"python")
 assert v.shape==q.shape and np.isfinite(v).all()

def test_bh():
 q=benjamini_hochberg([.01,.2,.03]); assert np.all((q>=0)&(q<=1))
