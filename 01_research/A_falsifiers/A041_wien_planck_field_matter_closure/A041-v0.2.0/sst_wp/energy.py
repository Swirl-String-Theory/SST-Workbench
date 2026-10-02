from __future__ import annotations
import math
from .kernels import energy_sum
from . import action_constants as C

def physical_scales(core_fraction):
    L=C.r_c/core_fraction
    Gamma=C.Gamma_c
    t=L*L/Gamma
    return {'L_phys_m':L,'Gamma_phys_m2_s':Gamma,'time_scale_s':t,'rho_f_kg_m3':C.rho_f}

def physical_line_energy(points,offsets,core_fraction,require_native=False):
    s=energy_sum(points,offsets,core_fraction,require_native)
    sc=physical_scales(core_fraction)
    E=C.rho_f*sc['Gamma_phys_m2_s']**2*sc['L_phys_m']/(8*math.pi)*s
    return float(E),float(s),sc
