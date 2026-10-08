import numpy as np
from experiment.metrics import biot_savart, total_energy_length


def circle(n=128):
    a=np.linspace(0,2*np.pi,n,endpoint=False)
    return np.column_stack([np.cos(a),np.sin(a),np.zeros_like(a)])


def test_orientation_reversal_and_energy():
    p=circle()
    q=np.array([[0.,0.,2.],[0.2,0.1,1.5]])
    v=biot_savart(p,q,1.0,0.05)
    vr=biot_savart(p[::-1].copy(),q,1.0,0.05)
    rel=np.linalg.norm(v+vr)/np.linalg.norm(v)
    assert rel < 1e-12
    assert total_energy_length([p],0.05) > 0
