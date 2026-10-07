import numpy as np
from a054_ntaf.geometry import torus_link_3_3,rotate_components
from a054_ntaf.physics import evaluate_static,fibonacci_sphere,separation_energy_response,circulation_vector


def test_objectivity_static_metrics():
    c=torus_link_3_3(72)
    a=0.4; R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1.]])
    d=fibonacci_sphere(96); x=evaluate_static(c,0.02,'S1',far_dirs=d,backend='numpy_reference'); y=evaluate_static(rotate_components(c,R),0.02,'S1',far_dirs=d@R.T,backend='numpy_reference')
    for k in ['rel_eq_residual','cross_stabilization','farfield_anisotropy_r6','separation_curvature_median_norm']:
        assert abs(x[k]-y[k])<1e-6


def test_separation_response_finite():
    c=torus_link_3_3(48); g=circulation_vector(3,'Q1')
    r=separation_energy_response(c,g,0.02,epsilon=.035)
    assert np.isfinite(r['separation_curvature_median_norm'])
    assert len(r['separation_mode_curvatures_norm'])==3
