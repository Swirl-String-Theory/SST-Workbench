from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from euler_tangent import Euler3D,load_geometry,initial_condition
from kelvin_spectrum import compute_spectrum,operator,finite_difference_check
from wavepackets import integrate_packets,arc_map,packet,diagnostics
P=ROOT/'data/knot_3.1.txt'

def test_real_euler_operator_agrees_with_direct_rhs():
    g=Euler3D(8,.4);geom,_=load_geometry(P);U,D,*_=initial_condition(g,geom)
    op,_=operator(g,U)
    _,tangent=g.rhs(U,D[:1])
    assert np.linalg.norm(op@D[0].ravel()-tangent[0].ravel())<1e-10

def test_finite_difference_tangent_jacobian():
    g=Euler3D(8,.4);geom,_=load_geometry(P);U,D,*_=initial_condition(g,geom)
    assert finite_difference_check(g,U,D[0])<1e-6

def test_spectrum_actual_eigen_residuals_and_base_not_steady():
    res=compute_spectrum(P,n=8)
    assert len(res['candidates'])==4
    assert max(x['relative_residual'] for x in res['candidates'])<1e-5
    assert res['nonstationary_rate']>1e-4

def test_initial_wavepackets_solenoidal_and_separate():
    g=Euler3D(12,.4);geom,_=load_geometry(P)
    from euler_tangent import normalized_components
    s,r,total=arc_map(g,normalized_components(geom)[0])
    a=packet(g,s,r,total,.14*total,+1);b=packet(g,s,r,total,-.14*total,-1)
    for d in [a.real,a.imag,b.real,b.imag]:assert g.divergence_relative(d)<1e-9
    assert np.linalg.norm(a-b)>1
    assert 0<diagnostics(a,b,s,r,total)['A_detector']<1

def test_superposition_complex_quadratures():
    g=Euler3D(8,.4);geom,_=load_geometry(P);U,D,*_=initial_condition(g,geom)
    both=np.stack([D[0],D[1],D[0]+D[1]])
    _,new=g.rk4(U,both,.07)
    assert np.linalg.norm(new[2]-new[0]-new[1])/(np.linalg.norm(new[2])+1e-30)<1e-12

def test_no_background_no_packet_transport():
    f,result=integrate_packets(P,n=8,steps=8,dt=.05,no_flow=True)
    assert abs(float(f.A_detector.iloc[-1]-f.A_detector.iloc[0]))<1e-10
    assert abs(float(f.B_detector.iloc[-1]-f.B_detector.iloc[0]))<1e-10

def test_two_packets_run_without_asserting_collision():
    f,result=integrate_packets(P,n=8,steps=6,dt=.04)
    assert all(np.isfinite(f.detector_total))
    assert abs(float(f.detector_total.iloc[1]-f.A_detector.iloc[1]-f.B_detector.iloc[1]-f.detector_cross.iloc[1]))<1e-10
    assert result['max_divergence']<1e-10
    assert isinstance(result['verified_collision'],bool)
