import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from microgravity.geometry import providers
from microgravity.monopole import source_gradient,source_potential,force,force_pair,fit_slope,cross_stress_integral,euler_pressure_monopole_analytic,weights

def test_providers_both():
    p=providers(48);assert set(p)=={'gilbert','knotplot'}
    assert all(len(q['raw_sha256'])==64 for q in p.values())
def test_gauss_weights():
    x=providers(48)['gilbert']['x'];assert abs(sum(weights(x)[1])-1)<1e-14
def test_closed_scalar_farfield():
    x=providers(96)['gilbert']['x'];n,_=fit_slope(x,x);assert abs(n-2)<0.05
def test_action_reaction():
    x=providers(96)['knotplot']['x'];f,g=force_pair(x,x,5);assert np.linalg.norm(f+g)/np.linalg.norm(f)<0.002
def test_cross_stress():
    x=providers(96)['gilbert']['x'];f=force(x,x,5);s=cross_stress_integral(x,x,5,nsurf=500)
    assert np.linalg.norm(f+s)/np.linalg.norm(f)<0.05
def test_potential_gradient():
    x=providers(48)['gilbert']['x'];pt=np.array([[.2,.1,6.]])
    h=1e-4;dz=np.array([[0,0,h]])
    fd=(source_potential(pt+dz,x)-source_potential(pt-dz,x))/(2*h)
    assert abs(fd[0]-source_gradient(pt,x)[0,2])<1e-8
def test_euler_zero_integral():
    assert euler_pressure_monopole_analytic(None)==0
