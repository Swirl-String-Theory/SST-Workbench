import os
import numpy as np
import pytest


def test_native_kernels_if_requested():
    if os.environ.get('SST_BACKEND','').lower() != 'native':
        pytest.skip('native backend not requested')
    from sst_vortex_shear import backend
    from sst_vortex_shear.filaments import hopf_cell, filament_energy_python
    a=np.array([[1.,2.,3.],[0.2,-0.7,0.4]])
    b=np.array([[-1.,4.,0.5],[0.8,0.3,-1.1]])
    assert np.max(np.abs(backend.cross_product(a,b)-np.cross(a,b))) < 1e-12
    h=hopf_cell(1.0,24,True)
    assert abs(backend.filament_energy(h,[1.,1.],0.18)-filament_energy_python(h,[1.,1.],0.18)) < 1e-11
