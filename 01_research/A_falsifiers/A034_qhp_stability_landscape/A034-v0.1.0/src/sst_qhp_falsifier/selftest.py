from pathlib import Path
import tempfile,json,numpy as np
from .geometry import resample_closed,best_cyclic_align,normal_component
from .solver import velocity_material,backend_name
from .demo import make_demo

def selftest():
    t=np.linspace(0,2*np.pi,96,endpoint=False); x=np.c_[np.cos(t),np.sin(t),.1*np.sin(2*t)]; y=np.roll(x@np.array([[0,-1,0],[1,0,0],[0,0,1.]]).T,17,axis=0); ya,al=best_cyclic_align(y,x); assert al['mse']<1e-20
    ref=np.linalg.norm(np.roll(x,-1,axis=0)-x,axis=1); u,c=velocity_material(x,1.,.05,ref,-.5,False); assert np.isfinite(u).all() and len(c)==len(x)
    return {'pass':True,'alignment_mse':al['mse'],'backend':backend_name(),'msvc_ssize_guard':'py::ssize_t'}
