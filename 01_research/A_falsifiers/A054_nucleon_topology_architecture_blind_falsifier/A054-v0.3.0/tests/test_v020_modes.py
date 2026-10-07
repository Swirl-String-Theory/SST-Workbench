import numpy as np
from a054_ntaf.geometry import torus_link_3_3
from a054_ntaf.modes_v020 import build_mode_basis, family_indices


def test_v020_basis_is_orthonormal_and_has_families():
    c=torus_link_3_3(36)
    m=build_mode_basis(c,(1,),True,True)
    B=m['basis'].reshape(len(m['basis']),-1)
    G=B@B.T
    assert np.max(np.abs(G-np.eye(len(B))))<1e-8
    for f in ('separation','breathing','torsion','kelvin'):
        assert len(family_indices(m,f))>0
