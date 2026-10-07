import numpy as np
from a054_ntaf.geometry import torus_link_3_3
from a054_ntaf.modes_v020 import build_mode_basis
from a054_ntaf.certify_v020 import relative_return_monodromy, separation_energy_hessian
from a054_ntaf.physics import circulation_vector


def test_no_rpo_means_no_floquet():
    c=torus_link_3_3(30); mi=build_mode_basis(c,(1,),True,True)
    cfg={'rpo_dt':1e-4,'floquet_modes_max':4,'floquet_eps':1e-3}
    out=relative_return_monodromy(c,circulation_vector(3,'Q1'),0.02,mi,{'accepted':False},cfg,'numpy_reference')
    assert out['evaluated'] is False
    assert out['status']=='NOT_EVALUATED_NO_RPO'


def test_separation_hessian_is_symmetric_finite():
    c=torus_link_3_3(30); mi=build_mode_basis(c,(1,),True,True)
    h=separation_energy_hessian(c,circulation_vector(3,'Q1'),0.02,mi,0.01)
    H=np.asarray(h['normalized_hessian'])
    assert np.isfinite(H).all()
    assert np.max(np.abs(H-H.T))<1e-10
