from __future__ import annotations
import math

# REVEAL-ONLY canonical values.
# This module MUST NOT be imported by campaign.py, energy.py, action_prepare.py,
# action_analyze.py, dynamics.py, kernels.py, modal.py, perturb.py,
# geometry.py, relative_equilibrium.py, or blind_guard.py.

v_swirl = 1.09384563e6
r_c = 1.40897017e-15
rho_core = 3.8934358266918687e18
rho_f = 7.0e-7
F_swirl_max = 29.053507
F_gr_max = 3.02563e43
c = 299792458.0
alpha = 7.2973525643e-3
h = 6.62607015e-34
hbar = h/(2*math.pi)
Gamma_c = 2*math.pi*r_c*v_swirl
