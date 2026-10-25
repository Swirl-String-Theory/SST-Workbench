"""VCCR v0.1.0. Analytic, conditional, non-dynamical conservation closure.
Units: all physical inputs SI; geometry coordinates retain the user's original units.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, asdict
from typing import Sequence

SWIRL_SPEED = 1.09384563e6                  # m / s
CORE_RADIUS = 1.40897017e-15                # m
FLUID_DENSITY = 7.0e-7                      # kg / m^3
CORE_DENSITY = 3.8934358266918687e18        # kg / m^3 -- NOT interchangeable with rho_f
TREFOIL_ROPELENGTH_DIAMETER = 16.3714672385  # dimensionless, *numerical* reference, not an exact mathematical minimum

@dataclass(frozen=True)
class State:
    L_m: float
    a_m: float
    diameter_m: float
    volume_m3: float
    circulation_m2_s: float
    mean_omega_s1: float
    swirl_edge_speed_m_s: float
    ropelength_diameter: float
    ropelength_radius: float
    fluid_mass_kg: float


def finite_positive(value: float, name: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f'{name} must be finite and strictly positive, got {value!r}')
    return x


def state_from_length(L_m: float, volume_m3: float, circulation_m2_s: float, density_kg_m3: float = FLUID_DENSITY) -> State:
    L = finite_positive(L_m, 'L_m')
    V = finite_positive(volume_m3, 'volume_m3')
    G = finite_positive(circulation_m2_s, 'circulation_m2_s')
    density = finite_positive(density_kg_m3, 'density_kg_m3')
    a = math.sqrt(V / (math.pi * L))
    if a == 0.0 or not math.isfinite(a):
        raise ValueError('underflow or overflow in core radius')
    return State(L, a, 2*a, V, G, G/(math.pi*a*a), G/(2*math.pi*a), L/(2*a), L/a, density*V)


def reference_trefoil(a0:float=CORE_RADIUS, swirl_speed:float=SWIRL_SPEED, R_d:float=TREFOIL_ROPELENGTH_DIAMETER,
                      density_kg_m3:float=FLUID_DENSITY) -> State:
    a = finite_positive(a0, 'a0')
    v = finite_positive(swirl_speed, 'swirl_speed')
    rd = finite_positive(R_d, 'ropelength_diameter')
    # Fixed physical calibration: assume the physical core fills an ideal trefoil's geometric tube.
    L = 2*a*rd
    V = math.pi*a*a*L
    G = 2*math.pi*a*v
    return state_from_length(L,V,G,density_kg_m3)


def state_from_ropelength_saturated(R_d:float, volume_m3:float, circulation_m2_s:float,
                                      density_kg_m3:float=FLUID_DENSITY) -> State:
    # CONDITIONAL: physical core radius equals geometric tube thickness (radius).
    rd = finite_positive(R_d,'R_d')
    V = finite_positive(volume_m3,'volume_m3')
    a = (V/(2*math.pi*rd))**(1/3)
    L = 2*a*rd
    return state_from_length(L, V, circulation_m2_s, density_kg_m3)


def knot_type_bounds(volume_m3:float, Rmin_d:float) -> dict:
    """Necessary length bound and radius bound for an embedded uniform tube.
    Requires trustworthy *minimum* diameter-convention ropelength for that knot.
    """
    V=finite_positive(volume_m3,'V'); R=finite_positive(Rmin_d,'Rmin_d')
    Lmin=(4*V*R*R/math.pi)**(1/3)
    amax=(V/(2*math.pi*R))**(1/3)
    return dict(L_min_m=Lmin, radius_max_m=amax, rope_min_d=R, assumption='externally supplied minimum ropelength; uniform embedded tube')


def stretch_table(stretch_factors:Sequence[float], ref:State) -> list[dict]:
    rows=[]
    for f in stretch_factors:
        sf=finite_positive(f,'stretch_factor')
        s=state_from_length(ref.L_m*sf,ref.volume_m3,ref.circulation_m2_s,ref.fluid_mass_kg/ref.volume_m3)
        r=asdict(s)
        r.update(stretch_factor=sf, radius_ratio=s.a_m/ref.a_m,
                 mean_omega_ratio=s.mean_omega_s1/ref.mean_omega_s1,
                 edge_speed_ratio=s.swirl_edge_speed_m_s/ref.swirl_edge_speed_m_s)
        rows.append(r)
    return rows


def dimension_checks(ref:State) -> dict:
    checks={
        'V_reconstructed': math.isclose(math.pi*ref.a_m**2*ref.L_m,ref.volume_m3,rel_tol=1e-12),
        'circulation_reconstructed': math.isclose(ref.mean_omega_s1*math.pi*ref.a_m**2,ref.circulation_m2_s,rel_tol=1e-12),
        'R_d_definition': math.isclose(ref.L_m/ref.diameter_m,ref.ropelength_diameter,rel_tol=1e-12),
        'v_edge_reconstructed': math.isclose(ref.circulation_m2_s/(2*math.pi*ref.a_m),ref.swirl_edge_speed_m_s,rel_tol=1e-12),
    }
    return checks
