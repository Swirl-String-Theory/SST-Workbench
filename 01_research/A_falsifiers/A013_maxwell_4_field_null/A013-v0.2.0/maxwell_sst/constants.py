from __future__ import annotations
import math

V_SWIRL = 1.09384563e6          # m s^-1
R_C = 1.40897017e-15            # m; horn/circulation radius
RHO_CORE = 3.8934358266918687e18 # kg m^-3
RHO_REF = 7.0e-7                # kg m^-3; legacy/reference normalization in Canon v0.8.35
GAMMA0 = 2.0 * math.pi * R_C * V_SWIRL

DEFAULTS = {
    "stokes_rel": 1.0e-4,
    "holonomy_rel": 3.0e-2,
    "moving_loop_rel": 1.0e-4,
    "exterior_curl_rel": 8.0e-2,
    "exterior_div_rel": 8.0e-2,
    "beltrami_rel": 1.0e-3,
    "cyclic_work_rel": 1.0e-6,
    "radial_coherence": 0.90,
    "radial_exponent_tol": 0.25,
    "radial_flux_cv": 0.15,
}
