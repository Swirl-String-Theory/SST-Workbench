import numpy as np
from sst_blind.multitopology import build_generic_modes, generic_jacobian


def test_fast_jacobian_total_only_no_empty_component_projection():
    # This reproduces the v0.4.6 failure without requiring a GPU: the fast
    # decompose=False path returns only total velocity and empty diagnostic
    # ledgers. generic_jacobian must never project those empty lists.
    n=48
    t=np.linspace(0,2*np.pi,n,endpoint=False)
    c=np.column_stack([np.cos(t), np.sin(t), 0.08*np.sin(2*t)])
    comps=[c]
    mi=build_generic_modes(comps, kelvin_harmonics=(2,))
    out=generic_jacobian(comps,mi,eps=0.004,gamma=1.0,core=0.04,
                         backend='python',allow_sycl_cpu=False,mod=None,local_span=4)
    assert set(out['J']) == {'total'}
    J=out['J']['total']
    assert J.shape == (len(mi['modes']), len(mi['modes']))
    assert np.all(np.isfinite(J))
    assert set(out['eigs']) == {'total'}
