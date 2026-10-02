"""
Minimal numerical checks for SST v0.8.15 pressure--optical locking.
This is not a full PDE solver; it validates constants and leading-order scaling.
"""
from math import sqrt

c = 2.99792458e8
rho_f = 7.0e-7
v_swirl = 1.09384563e6
r_c = 1.40897017e-15

pressure_deficit = 0.5 * rho_f * v_swirl**2
locking_coeff = 1.0 / (rho_f * c**2)
delta_n_linear = pressure_deficit * locking_coeff
n_exact_minus_1 = 1.0 / sqrt(1.0 - v_swirl**2 / c**2) - 1.0
omega_c = v_swirl / r_c
alpha_grav_candidate = (r_c / v_swirl) ** 2

print(f"0.5 rho_f v_swirl^2 = {pressure_deficit:.10e} Pa")
print(f"1/(rho_f c^2)      = {locking_coeff:.10e} Pa^-1")
print(f"delta n linear     = {delta_n_linear:.10e}")
print(f"n_exact - 1        = {n_exact_minus_1:.10e}")
print(f"relative error     = {(delta_n_linear-n_exact_minus_1)/n_exact_minus_1:.10e}")
print(f"omega_c            = {omega_c:.10e} s^-1")
print(f"omega_c^-2         = {alpha_grav_candidate:.10e} s^2")
