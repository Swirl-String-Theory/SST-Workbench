
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SST Bulk-Signal Bounds (lab utility)
------------------------------------
Functions:
- cp_from_constants(rho_core, rho_f, c): compute c_P = sqrt((rho_core * c^2)/rho_f)
- cp_lower_bound(delta_L, delta_t): bound from latency-vs-distance slope test
- epsilon_upper_bound(L, P_src, K, T_int, B, R_ohm, Temp_K, SNR_min=5.0): null-result coupling bound

Units:
- rho_core [kg/m^3], rho_f [kg/m^3], c [m/s]
- delta_L, L [m]; delta_t [s]
- P_src [W]; K [V·m^2/W]; T_int [s]; B [Hz]; R_ohm [Ω]; Temp_K [K]
- Returns: c_P [m/s], epsilon [dimensionless]

Example usage is provided in __main__.
"""

from math import sqrt, pi

k_B = 1.380649e-23  # J/K (Boltzmann constant)

def cp_from_constants(rho_core: float, rho_f: float, c: float) -> float:
    """Compute c_P from canonical constants: c_P = sqrt((rho_core * c^2)/rho_f)."""
    if rho_core <= 0 or rho_f <= 0 or c <= 0:
        raise ValueError("All inputs must be positive.")
    B_eff = rho_core * (c**2)  # J/m^3
    return sqrt(B_eff / rho_f)

def cp_lower_bound(delta_L: float, delta_t: float) -> float:
    """Lower bound on c_P from slope test: c_P >= delta_L / delta_t."""
    if delta_L <= 0:
        raise ValueError("delta_L must be positive.")
    if delta_t <= 0:
        # If delta_t is below resolution, use that resolution value externally.
        raise ValueError("delta_t must be positive (use instrument timing resolution).")
    return delta_L / delta_t

def epsilon_upper_bound(L: float, P_src: float, K: float, T_int: float, B: float,
                        R_ohm: float, Temp_K: float, SNR_min: float = 5.0) -> float:
    """
    Upper bound on coupling epsilon from a null detection (no matched-filter peak).

    Signal model (per your notes):
        V_sig(L) = epsilon * K * P_src / (4*pi*L^2)
    Noise (thermal + amp approximation):
        V_n = sqrt(4 * k_B * Temp_K * R_ohm * B)
    Matched-filter SNR gain ~ sqrt(B * T_int)
    Detection criterion: SNR < SNR_min => epsilon <= ...

    Returns epsilon (dimensionless).
    """
    if L <= 0 or P_src <= 0 or K <= 0 or T_int <= 0 or B <= 0 or R_ohm <= 0 or Temp_K <= 0 or SNR_min <= 0:
        raise ValueError("All inputs must be positive.")
    Vn = (4.0 * k_B * Temp_K * R_ohm * B) ** 0.5
    # Rearranged inequality for epsilon:
    # epsilon <= (4*pi*L^2 / (K * P_src)) * SNR_min * Vn / sqrt(B * T_int)
    from math import sqrt as _sqrt
    eps = (4.0 * pi * (L**2) / (K * P_src)) * (SNR_min * Vn) / _sqrt(B * T_int)
    return eps

if __name__ == "__main__":
    # Canonical constants (user-provided SST values)
    rho_core = 3.8934358266918687e18   # kg/m^3
    rho_f    = 7.0e-7                  # kg/m^3
    c        = 2.99792458e8            # m/s

    cp = cp_from_constants(rho_core, rho_f, c)
    print(f"c_P (from constants) = {cp:.6e} m/s (~{cp/c:.3e} c)")

    # Example slope test (instrument resolution-limited latency difference)
    delta_L = 90.0               # m (e.g., 100 m - 10 m)
    delta_t = 100e-12            # s (100 ps timing resolution)
    cp_lb = cp_lower_bound(delta_L, delta_t)
    print(f"c_P lower bound from slope test = {cp_lb:.6e} m/s (~{cp_lb/c:.3e} c)")

    # Example null-result coupling bound
    L       = 100.0              # m
    P_src   = 10.0               # W (source burst power)
    K       = 1e-3               # V·m^2/W (example transduction factor)
    T_int   = 10.0               # s integration
    B       = 1e6                # Hz equivalent noise bandwidth of matched filter
    R_ohm   = 50.0               # Ω
    Temp_K  = 300.0              # K
    SNR_min = 5.0
    eps_ub = epsilon_upper_bound(L, P_src, K, T_int, B, R_ohm, Temp_K, SNR_min)
    print(f"""epsilon upper bound (null) = {eps_ub:.6e}
Units: dimensionless
(Parameters: L={L} m, P_src={P_src} W, K={K} V·m^2/W, T_int={T_int} s, B={B} Hz, R={R_ohm} Ω, T={Temp_K} K, SNR_min={SNR_min})""")
