import numpy as np
from sst_torsion.models import kelvin_omega,torsion_omega,power_law_fit
from sst_torsion.fitting import classify_dispersion

def test_power_exponents():
    k=np.arange(1.0,11.0)
    assert abs(power_law_fit(k,kelvin_omega(k,0.2))['p']-2.0)<1e-12
    assert abs(power_law_fit(k,torsion_omega(k,1.1,0.0))['p']-1.0)<1e-12

def test_classifier_clean():
    k=np.arange(1.0,11.0)
    assert classify_dispersion(k,kelvin_omega(k,0.2))['classification']=='KELVIN_QUADRATIC'
    assert classify_dispersion(k,torsion_omega(k,1.1,0.1))['classification']=='TORSIONAL_LINEAR_GAPPED'
