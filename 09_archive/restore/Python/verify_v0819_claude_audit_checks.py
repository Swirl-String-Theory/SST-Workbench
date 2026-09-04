#!/usr/bin/env python3
"""
Numerical consistency checks for SST_CANON v0.8.19 Claude-audit cleanup.
This script is deliberately standalone: it uses explicit constants stated in the
Canon/CODATA-compatible chain rather than importing SSTcore.
"""
import math

# Canon/CODATA-compatible constants used in SST v0.8.x checks.
c = 299_792_458.0                 # m/s, exact
alpha = 7.297_352_5643e-3         # fine-structure constant
hbar = 1.054_571_817e-34          # J s
R_inf = 10_973_731.568_160        # m^-1, Rydberg constant
r_c = 1.408_970_17e-15            # m, canon horn/circulation radius
rho_horn = 3.893_435_826_691_8687e18  # kg/m^3, canon effective horn density
lambda_c = 2.426_310_238_67e-12   # m, electron Compton wavelength h/(m_e c)

# Groningen/Foucault benchmark constants.
phi_deg = 53.219
Omega_earth = 7.292_115_0e-5      # rad/s, sidereal Earth rotation
R_eq = 6_378_137.0                # m, WGS84 equatorial radius; matches prior Groningen benchmark
R_mean = 6_371_000.0              # m, spherical mean comparison
seconds_per_day = 86_400.0
g0 = 9.80665                      # m/s^2
height = 100.0                    # m


def fmax_from_rydberg() -> float:
    return 16 * math.pi**2 * hbar * R_inf**2 * c / alpha**5


def fmax_wrong_old_32() -> float:
    return 32 * math.pi**2 * hbar * R_inf**2 * c / alpha**5


def fmax_from_h_alpha_c() -> float:
    h = 2 * math.pi * hbar
    return h * alpha * c / (8 * math.pi * r_c**2)


def geometric_baseline_dimension() -> float:
    """Return kg-valued dimensional scale rho_horn*r_c^5/lambda_c^2."""
    return rho_horn * r_c**5 / lambda_c**2


def foucault_benchmark(radius: float) -> dict[str, float]:
    phi = math.radians(phi_deg)
    Omega_F = Omega_earth * math.sin(phi)
    T_F_hours = 2 * math.pi / Omega_F / 3600
    v_rot = Omega_earth * radius * math.cos(phi)
    S_rot = math.sqrt(1 - (v_rot / c) ** 2)
    dt_rot_ns_day = (1 - S_rot) * seconds_per_day * 1e9
    dt_h_ns_day = (g0 * height / c**2) * seconds_per_day * 1e9
    return {
        "Omega_F_s^-1": Omega_F,
        "T_F_hours": T_F_hours,
        "v_rot_m_s": v_rot,
        "one_minus_S_rot": 1 - S_rot,
        "dt_rot_ns_per_day": dt_rot_ns_day,
        "dt_height_100m_ns_per_day": dt_h_ns_day,
    }


def main() -> None:
    F16 = fmax_from_rydberg()
    F32 = fmax_wrong_old_32()
    Fhac = fmax_from_h_alpha_c()
    print("Rydberg--Fmax check")
    print(f"  16*pi^2 route: {F16:.12g} N")
    print(f"  old 32*pi^2 route: {F32:.12g} N  (factor {F32/F16:.6f})")
    print(f"  h*alpha*c/(8*pi*r_c^2): {Fhac:.12g} N")
    print(f"  relative 16-route vs h-alpha-c route: {(F16/Fhac - 1):.3e}")
    print()

    geom = geometric_baseline_dimension()
    print("Geometric baseline dimension check")
    print("  rho_horn*r_c^5/lambda_c^2 has SI units kg/m^3*m^5/m^2 = kg")
    print(f"  numerical scale: {geom:.12e} kg")
    print()

    print("Foucault/Groningen benchmark, phi = 53.219 deg")
    for label, radius in [("WGS84 equatorial radius", R_eq), ("mean spherical radius", R_mean)]:
        d = foucault_benchmark(radius)
        print(f"  {label} R={radius:g} m")
        for k, v in d.items():
            print(f"    {k}: {v:.12g}")
    print()
    print("Notes")
    print("  The 37.28 ns/day rotational value corresponds to the WGS84/equatorial-radius benchmark.")
    print("  The spherical-mean radius gives about 37.20 ns/day; this is a radius-convention difference, not an algebraic discrepancy.")


if __name__ == "__main__":
    main()
