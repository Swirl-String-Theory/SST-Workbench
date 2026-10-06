import numpy as np
from a054_ntaf.geometry import torus_link_3_3,borromean_braid,unlinked_three_rings,pairwise_link_matrix,total_length

def test_t33_pairwise_linking():
    M=pairwise_link_matrix(torus_link_3_3(360))
    vals=M[np.triu_indices(3,1)]
    assert np.all(np.abs(np.abs(vals)-1)<0.08), vals

def test_borromean_pairwise_zero():
    comps=borromean_braid(360)
    assert len(comps)==3
    M=pairwise_link_matrix(comps)
    assert np.max(np.abs(M))<0.08, M

def test_unlinked_zero_and_length():
    c=unlinked_three_rings(180); M=pairwise_link_matrix(c)
    assert np.max(np.abs(M))<0.05
    assert abs(total_length(c)-1)<1e-9

def test_connected_sum_decorator_preserves_link_skeleton():
    from a054_ntaf.composite import decorate_skeleton
    t=np.linspace(0,2*np.pi,192,endpoint=False); R=2.; r=.7
    knot=np.c_[(R+r*np.cos(3*t))*np.cos(2*t),(R+r*np.cos(3*t))*np.sin(2*t),r*np.sin(3*t)]
    for skeleton in (torus_link_3_3(192),borromean_braid(192)):
        before=pairwise_link_matrix(skeleton)
        after,cert=decorate_skeleton(skeleton,[knot,knot,knot],n=192)
        assert cert['status']=='CERTIFIED_SAMPLED_CONNECTED_SUM'
        assert np.max(np.abs(pairwise_link_matrix(after)-before))<0.01
