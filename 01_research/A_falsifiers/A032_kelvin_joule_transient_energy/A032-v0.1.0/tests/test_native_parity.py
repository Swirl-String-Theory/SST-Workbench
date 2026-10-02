import numpy as np
import pytest
from native_ext.core import _load_cpp_backend
from native_ext.fallback import biot_savart as py_biot,filament_hamiltonian as py_h

def test_native_parity_if_available():
 mod=_load_cpp_backend(skip_build=True)
 if mod is None:pytest.skip('native extension not built')
 t=np.linspace(0,2*np.pi,48,endpoint=False);p=np.c_[np.cos(t),np.sin(t),.2*np.sin(3*t)];q=p[::3].copy()
 vc=np.asarray(mod.biot_savart(p,q,1.2,0.15,False,False));vp=py_biot(p,q,1.2,0.15);assert np.allclose(vc,vp,rtol=2e-12,atol=2e-13)
 hc=float(mod.filament_hamiltonian(p,0.7,1.2,0.15,False,False));hp=py_h(p,0.7,1.2,0.15);assert np.isclose(hc,hp,rtol=2e-12,atol=1e-14)
