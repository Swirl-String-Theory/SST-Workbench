from __future__ import annotations

def dimensional_action_scale(rho_kg_m3, gamma_m2_s, length_m):
    """
    Reveal-only dimensional action scale:

        J0 = rho * Gamma * L^3  [J s]

    All values are supplied explicitly by the reveal normalization file.
    """
    rho = float(rho_kg_m3)
    gamma = float(gamma_m2_s)
    length = float(length_m)
    return rho * gamma * length**3
