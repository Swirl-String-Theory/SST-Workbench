"""Canonical constants used only for declared SST scale checks."""

K_B_J_PER_K = 1.380649e-23
EV_J = 1.602176634e-19

V_SWIRL = 1.09384563e6  # m/s
R_C = 1.40897017e-15  # m
RHO_F = 7.0e-7  # kg/m^3
F_SWIRL_MAX = 29.053507  # N
F_GR_MAX = 3.02563e43  # N

P_SUBSTRATE_0 = 0.5 * RHO_F * V_SWIRL**2
OMEGA_SST = V_SWIRL / R_C
