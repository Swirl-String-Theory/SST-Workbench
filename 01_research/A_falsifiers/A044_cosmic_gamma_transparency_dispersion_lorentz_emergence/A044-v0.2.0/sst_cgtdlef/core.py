from __future__ import annotations
import hashlib, json, math
from pathlib import Path
from typing import Iterable, Sequence

MPC_M = 3.085677581491367e22
M_E_EV = 0.510998950e6

try:
    from . import _native  # type: ignore
except Exception:
    _native = None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dump_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def poisson_at_least_one(lam: float) -> float:
    if _native is not None:
        return float(_native.poisson_at_least_one(lam))
    if lam < 0:
        raise ValueError("lambda must be non-negative")
    return -math.expm1(-lam)


def dispersion_epsilon(E_GeV: float, E_star_GeV: float, n: int) -> float:
    if _native is not None:
        return float(_native.dispersion_epsilon(E_GeV, E_star_GeV, n))
    if E_GeV <= 0 or E_star_GeV <= 0 or n not in (1, 2):
        raise ValueError("Require E>0, E_star>0, n in {1,2}")
    return (E_GeV / E_star_GeV) ** n


def group_velocity_fraction_exact(E_GeV: float, E_star_GeV: float, n: int) -> float:
    if _native is not None and hasattr(_native, "group_velocity_fraction_exact"):
        return float(_native.group_velocity_fraction_exact(E_GeV, E_star_GeV, n))
    x = dispersion_epsilon(E_GeV, E_star_GeV, n)
    return math.sqrt(1.0 + x) / (1.0 + (1.0 + n / 2.0) * x)


def group_velocity_fraction_leading(E_GeV: float, E_star_GeV: float, n: int) -> float:
    x = dispersion_epsilon(E_GeV, E_star_GeV, n)
    return 1.0 - 0.5 * (n + 1.0) * x

def group_delay_fraction_exact(E_GeV: float, E_star_GeV: float, n: int) -> float:
    """Stable evaluation of delta = 1-v_g/c for tiny x.

    Direct subtraction 1-v loses precision for astrophysical scales.
    For v=sqrt(1+x)/(1+a x), rationalize the numerator.
    """
    x = dispersion_epsilon(E_GeV, E_star_GeV, n)
    a = 1.0 + 0.5*n
    den = 1.0 + a*x
    sq = math.sqrt(1.0+x)
    num = ((2.0*a-1.0)*x + a*a*x*x) / (1.0 + a*x + sq)
    return num/den


def pair_threshold_eV(E_TeV: float, E_star_GeV: float | None = None, n: int | None = None) -> float:
    if E_TeV <= 0:
        raise ValueError("E_TeV must be positive")
    E_eV = E_TeV * 1e12
    eps = M_E_EV * M_E_EV / E_eV
    if E_star_GeV is not None:
        if n not in (1, 2):
            raise ValueError("n must be 1 or 2")
        E_star_eV = E_star_GeV * 1e9
        eps += E_eV ** (n + 1) / (4.0 * E_star_eV ** n)
    return eps


def simpson_integral(fn, a: float, b: float, N: int = 4096) -> float:
    if N < 2:
        raise ValueError("N must be >=2")
    if N % 2:
        N += 1
    h = (b - a) / N
    s = fn(a) + fn(b)
    for i in range(1, N):
        s += (4.0 if i % 2 else 2.0) * fn(a + i * h)
    return s * h / 3.0


def cosmology_integral(z: float, n: int, Om: float, Ol: float, N: int = 4096) -> float:
    if z < 0 or n not in (1, 2):
        raise ValueError("Require z>=0 and n in {1,2}")
    return simpson_integral(lambda zp: (1.0 + zp) ** n / math.sqrt(Om * (1.0 + zp) ** 3 + Ol), 0.0, z, N)


def tof_delay_s(Eh_TeV: float, El_TeV: float, E_star_GeV: float, n: int,
                z: float, H0_km_s_Mpc: float, Om: float, Ol: float, N: int = 4096) -> float:
    H0 = H0_km_s_Mpc * 1000.0 / MPC_M
    Eh = Eh_TeV * 1e3
    El = El_TeV * 1e3
    I = cosmology_integral(z, n, Om, Ol, N)
    return 0.5 * (n + 1.0) * (Eh ** n - El ** n) / (E_star_GeV ** n) * I / H0


def invert_tof_scale_GeV(Eh_TeV: float, El_TeV: float, dt_s: float, n: int,
                         z: float, H0_km_s_Mpc: float, Om: float, Ol: float, N: int = 4096) -> float:
    if dt_s <= 0:
        raise ValueError("dt_s must be positive")
    H0 = H0_km_s_Mpc * 1000.0 / MPC_M
    Eh = Eh_TeV * 1e3
    El = El_TeV * 1e3
    I = cosmology_integral(z, n, Om, Ol, N)
    numer = 0.5 * (n + 1.0) * (Eh ** n - El ** n) * I / H0
    return (numer / dt_s) ** (1.0 / n)


def intersect(lowers: Sequence[float], uppers: Sequence[float]) -> dict:
    lo = max(lowers) if lowers else 0.0
    hi = min(uppers) if uppers else math.inf
    return {"lower": lo, "upper": hi, "nonempty": lo < hi,
            "log10_span": math.log10(hi / lo) if lo > 0 and math.isfinite(hi) and hi > lo else None}


def linear_fit_log_power(energies_GeV: Sequence[float], deltas: Sequence[float]) -> dict:
    pts = [(math.log(E), math.log(d)) for E, d in zip(energies_GeV, deltas) if E > 0 and d > 0]
    if len(pts) < 2:
        raise ValueError("Need at least two positive-delta samples")
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xm = sum(xs) / len(xs); ym = sum(ys) / len(ys)
    sxx = sum((x - xm) ** 2 for x in xs)
    slope = sum((x - xm) * (y - ym) for x, y in pts) / sxx
    intercept = ym - slope * xm
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in pts)
    ss_tot = sum((y - ym) ** 2 for y in ys)
    r2 = 1.0 if ss_tot == 0 else 1.0 - ss_res / ss_tot
    return {"n_eff": slope, "log_prefactor": intercept, "r2": r2, "count": len(pts)}


def implied_scales_GeV(energies_GeV: Sequence[float], deltas: Sequence[float], n: int) -> list[float]:
    out = []
    for E, d in zip(energies_GeV, deltas):
        if E > 0 and d > 0:
            out.append(E * ((n + 1.0) / (2.0 * d)) ** (1.0 / n))
    return out


def geometric_mean(xs: Iterable[float]) -> float:
    vals = [x for x in xs if x > 0]
    if not vals:
        raise ValueError("No positive values")
    return math.exp(sum(math.log(x) for x in vals) / len(vals))
