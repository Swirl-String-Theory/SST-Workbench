import os
import numpy as np
from .models import kelvin_omega as _py_kelvin, torsion_omega as _py_torsion, power_law_fit

def backend_name(): return os.environ.get('SST_BACKEND','python').lower()

def _native():
    import torsion_native
    return torsion_native

def kelvin_omega(k,beta):
    if backend_name()=='native': return np.asarray(_native().kelvin_omega(np.asarray(k,float),float(beta)))
    return _py_kelvin(k,beta)

def torsion_omega(k,c_phase,gap):
    if backend_name()=='native': return np.asarray(_native().torsion_omega(np.asarray(k,float),float(c_phase),float(gap)))
    return _py_torsion(k,c_phase,gap)

def loglog_slope(k,omega):
    if backend_name()=='native': return float(_native().loglog_slope(np.asarray(k,float),np.asarray(omega,float)))
    return float(power_law_fit(k,omega)['p'])
