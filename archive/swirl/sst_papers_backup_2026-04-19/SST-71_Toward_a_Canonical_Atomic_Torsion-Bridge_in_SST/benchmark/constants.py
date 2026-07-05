"""
Physical and SST canonical constants for the SST-71 helicity asymmetry benchmark.
All values in SI units; use J_to_eV for reporting in eV.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# SI fundamental constants
# ---------------------------------------------------------------------------
hbar: float = 1.054571817e-34   # J·s
e: float = 1.602176634e-19     # C
epsilon_0: float = 8.8541878128e-12  # F/m
c: float = 2.99792458e8         # m/s
m_e: float = 9.1093837015e-31   # kg
# Fine-structure constant alpha = e^2 / (4 pi epsilon_0 hbar c)
alpha: float = 7.2973525693e-3

# ---------------------------------------------------------------------------
# SST canonical constants (paper / Rosetta)
# ---------------------------------------------------------------------------
v_swirl: float = 1.09384563e6           # m/s
r_c: float = 1.40897017e-15             # m
rho_core: float = 3.8934358266918687e18 # kg/m^3
rho_f: float = 7.0e-7                   # kg/m^3
F_swirl_max: float = 29.053507          # N

# ---------------------------------------------------------------------------
# Derived SST / benchmark constants
# ---------------------------------------------------------------------------
eta_0: float = v_swirl / c
Omega_0: float = v_swirl / r_c
a0_sst: float = 2.0 * r_c / (alpha ** 2)
E_R: float = (hbar ** 2) / (2.0 * m_e * (a0_sst ** 2))

# Benchmark: expected helicity asymmetry when overlap magnitudes match
A_expected: float = -8.0 / 17.0  # ≈ -0.470588...

# eV conversion: 1 eV in J
eV_in_J: float = 1.602176634e-19


def J_to_eV(E_J: float) -> float:
    """Convert energy from joules to eV."""
    if E_J < 0:
        raise ValueError("Energy in J must be non-negative for conversion.")
    return E_J / eV_in_J


def eV_to_J(E_eV: float) -> float:
    """Convert energy from eV to joules."""
    return E_eV * eV_in_J


def print_constants_summary() -> None:
    """Print benchmark-relevant scales (eta_0, Omega_0, hbar*Omega_0 in eV, a0_sst, E_R in eV)."""
    print("SST-71 benchmark constants summary")
    print("-----------------------------------")
    print(f"  eta_0           = {eta_0:.6e}")
    print(f"  Omega_0         = {Omega_0:.6e} rad/s")
    print(f"  hbar*Omega_0    = {J_to_eV(hbar * Omega_0):.4f} eV")
    print(f"  a0_sst          = {a0_sst:.6e} m")
    print(f"  E_R             = {J_to_eV(E_R):.6f} eV")
    print(f"  A_expected      = {A_expected:.6f} (-8/17)")
    print("-----------------------------------")
