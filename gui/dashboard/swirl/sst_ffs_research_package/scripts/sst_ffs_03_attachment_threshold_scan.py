#!/usr/bin/env python3
"""
sst_ffs_03_attachment_threshold_scan.py

SST fractional-filament-sea attachment threshold scan.

This script takes the fractional filament-sea model

    theta_l(q) = (1/l) Theta(l*q0 - |q|)

and computes both:

    N_line      = q0/pi                         [m^-1]
    M2_line_l   = l^2 q0^3 / (3*pi)             [m^-3]
    <q^2>_l     = M2_line_l / N_line
                = l^2 q0^2 / 3                 [m^-2]

For an attachment / boundary-locking cutoff a_crit, define

    q_crit = 1/a_crit                           [m^-1]

and the clean dimensionless barrier

    B_l = <q^2>_l / q_crit^2
        = l^2 q0^2 / (3 q_crit^2)
        = l^2 (q0 a_crit)^2 / 3.

Interpretation:
    B_l < 1      attachment allowed by this spectral criterion
    B_l ~= 1     marginal / boundary-locking threshold
    B_l > 1      attachment suppressed / Pauli-like barrier

This is not a full hydrodynamic reconnection solver. It is a falsifiable
spectral threshold diagnostic for SST research-track scans.

Examples
--------
Standalone, using n_line = 0.5 um^-1:
    python sst_ffs_03_attachment_threshold_scan.py --n-line-um-inv 0.5 --outdir results_03

Use a summary from script 02:
    python sst_ffs_03_attachment_threshold_scan.py \
        --summary-csv results_02/sst_ffs_02_summary.csv \
        --spectrum-csv results_02/sst_ffs_02_spectrum.csv \
        --outdir results_03

Use the core radius as a_crit, or override:
    python sst_ffs_03_attachment_threshold_scan.py --a-crit-m 1.40897017e-15
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import numpy as np


# --- Canonical fallback constants ---
FALLBACK_V_SWIRL = 1.09384563e6       # m s^-1
FALLBACK_R_C = 1.40897017e-15         # m
FALLBACK_RHO_F = 7.0e-7               # kg m^-3
FALLBACK_GAMMA0 = 9.68361918e-9       # m^2 s^-1


# ---------------------------------------------------------------------------
# SSTcore bridge
# ---------------------------------------------------------------------------

def _try_get_attr(obj, names: Iterable[str]) -> Optional[float]:
    for name in names:
        try:
            if isinstance(obj, dict) and name in obj:
                return float(obj[name])
            if hasattr(obj, name):
                value = getattr(obj, name)
                if hasattr(value, "value"):
                    value = value.value
                return float(value)
        except Exception:
            pass
    return None


def load_sst_constants():
    v_swirl = FALLBACK_V_SWIRL
    r_c = FALLBACK_R_C
    rho_f = FALLBACK_RHO_F
    gamma0 = FALLBACK_GAMMA0
    source = "fallback canonical constants"

    try:
        import SSTcore as sst  # type: ignore

        candidates = [sst]
        for maybe in ("CONSTANTS", "constants", "canon", "SST_CONSTANTS"):
            if hasattr(sst, maybe):
                candidates.append(getattr(sst, maybe))

        for c in candidates:
            v = _try_get_attr(c, ("v_swirl", "V_SWIRL", "C_e", "Ce", "v_circlearrowleft"))
            if v is not None:
                v_swirl = v
                source = "SSTcore"
                break
        for c in candidates:
            rc = _try_get_attr(c, ("r_c", "R_c", "rc", "Rc", "core_radius"))
            if rc is not None:
                r_c = rc
                break
        for c in candidates:
            rho = _try_get_attr(c, ("rho_f", "rho_fluid", "rho_ae_fluid", "rho_effective"))
            if rho is not None:
                rho_f = rho
                break
        for c in candidates:
            gam = _try_get_attr(c, ("Gamma0", "GAMMA0", "gamma0", "Gamma_0", "circulation"))
            if gam is not None:
                gamma0 = gam
                break
    except Exception:
        pass

    return v_swirl, r_c, rho_f, gamma0, source


# ---------------------------------------------------------------------------
# CSV helpers
# ---------------------------------------------------------------------------

def read_key_value_csv(path: Path) -> dict[str, str]:
    """
    Read script-02 summary CSV:
        quantity,value,unit
    Returns quantity->value.
    """
    out: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return out
        for row in reader:
            key = (row.get("quantity") or "").strip()
            val = (row.get("value") or "").strip()
            if key:
                out[key] = val
    return out


def float_or_none(text: Optional[str]) -> Optional[float]:
    if text is None:
        return None
    try:
        return float(str(text).strip())
    except Exception:
        return None


def load_spectrum_csv(path: Path):
    """
    Load script-02 spectrum CSV with columns:
        q_m_inv,power
    """
    q_list = []
    p_list = []
    with path.open("r", newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = float_or_none(row.get("q_m_inv"))
            p = float_or_none(row.get("power"))
            if q is not None and p is not None and math.isfinite(q) and math.isfinite(p):
                q_list.append(q)
                p_list.append(max(0.0, p))
    if not q_list:
        raise ValueError(f"No usable q_m_inv,power rows in {path}")
    return np.asarray(q_list, dtype=float), np.asarray(p_list, dtype=float)


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ThresholdRow:
    ell: float
    q_edge_m_inv: float
    x1_m: float
    f_edge_hz: float
    n_line_m_inv: float
    m2_line_m_inv3: float
    q2_mean_m_inv2: float
    barrier_qcrit: float
    m2_line_ratio: float
    spectral_power_fraction: float
    classification: str


def classify_barrier(B: float, low: float = 0.8, high: float = 1.2) -> str:
    if not math.isfinite(B):
        return "unknown"
    if B < low:
        return "allowed"
    if B <= high:
        return "marginal"
    return "suppressed"


def contained_spectral_power(q: Optional[np.ndarray], p: Optional[np.ndarray], q_edge: float) -> float:
    if q is None or p is None:
        return float("nan")
    total = float(np.sum(p))
    if total <= 0.0:
        return float("nan")
    return float(np.sum(p[np.abs(q) <= q_edge]) / total)


def threshold_row(
    ell: float,
    q0: float,
    v_swirl: float,
    q_crit: float,
    m2_line_crit: Optional[float] = None,
    q: Optional[np.ndarray] = None,
    p: Optional[np.ndarray] = None,
) -> ThresholdRow:
    n_line = q0 / math.pi
    q_edge = ell * q0
    x1 = math.pi / q_edge if q_edge > 0.0 else float("nan")
    f_edge = v_swirl * q_edge / (2.0 * math.pi)
    m2_line = ell**2 * q0**3 / (3.0 * math.pi)
    q2_mean = m2_line / n_line if n_line > 0.0 else float("nan")
    barrier = q2_mean / (q_crit**2) if q_crit > 0.0 else float("nan")
    m2_ratio = m2_line / m2_line_crit if m2_line_crit and m2_line_crit > 0.0 else float("nan")
    frac = contained_spectral_power(q, p, q_edge)
    return ThresholdRow(
        ell=ell,
        q_edge_m_inv=q_edge,
        x1_m=x1,
        f_edge_hz=f_edge,
        n_line_m_inv=n_line,
        m2_line_m_inv3=m2_line,
        q2_mean_m_inv2=q2_mean,
        barrier_qcrit=barrier,
        m2_line_ratio=m2_ratio,
        spectral_power_fraction=frac,
        classification=classify_barrier(barrier),
    )


def resolve_q0(args, summary: dict[str, str]) -> tuple[float, str]:
    if args.q0 is not None:
        return float(args.q0), "--q0"

    if args.summary_csv is not None:
        q0 = float_or_none(summary.get("q0_m_inv"))
        if q0 is not None and q0 > 0.0:
            return q0, "summary:q0_m_inv"

        L = float_or_none(summary.get("length_m"))
        if L is not None and L > 0.0:
            return 2.0 * math.pi / L, "summary:length_m -> 2pi/L"

    if args.length_m is not None:
        return 2.0 * math.pi / float(args.length_m), "--length-m -> 2pi/L"

    if args.n_line_um_inv is not None:
        n_line = float(args.n_line_um_inv) * 1.0e6
        return math.pi * n_line, "--n-line-um-inv -> pi*n_line"

    raise ValueError("Could not resolve q0. Use --q0, --summary-csv, --length-m, or --n-line-um-inv.")


def resolve_ells(args) -> list[float]:
    if args.ells:
        return [float(e) for e in args.ells]
    if args.ell_max is None:
        return [1.0, 2.0, 4.0, 8.0, 13.0, 21.0, 34.0]
    start = float(args.ell_min)
    stop = float(args.ell_max)
    step = float(args.ell_step)
    if step <= 0.0:
        raise ValueError("--ell-step must be positive.")
    vals = []
    e = start
    while e <= stop + 1e-12:
        vals.append(e)
        e += step
    return vals


def write_scan_csv(path: Path, rows: list[ThresholdRow]) -> None:
    fields = list(ThresholdRow.__dataclass_fields__.keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: getattr(r, k) for k in fields})


def write_meta(path: Path, meta: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for k in sorted(meta):
            f.write(f"{k}={meta[k]}\n")


def save_barrier_plot(path: Path, rows: list[ThresholdRow]) -> None:
    import matplotlib.pyplot as plt

    ell = np.asarray([r.ell for r in rows], dtype=float)
    B = np.asarray([r.barrier_qcrit for r in rows], dtype=float)

    plt.figure()
    plt.plot(ell, B, marker="o")
    plt.axhline(1.0, linestyle="--", linewidth=0.9)
    plt.xlabel("ell")
    plt.ylabel("B_ell = <q^2>_ell / q_crit^2")
    plt.title("SST attachment threshold scan")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def save_power_plot(path: Path, rows: list[ThresholdRow]) -> None:
    import matplotlib.pyplot as plt

    ell = np.asarray([r.ell for r in rows], dtype=float)
    frac = np.asarray([r.spectral_power_fraction for r in rows], dtype=float)
    if np.all(~np.isfinite(frac)):
        return

    plt.figure()
    plt.plot(ell, frac, marker="o")
    plt.xlabel("ell")
    plt.ylabel("contained spectral power")
    plt.title("Spectrum power inside |q| <= ell q0")
    plt.tight_layout()
    plt.savefig(path, dpi=180)
    plt.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-csv", type=Path, default=None, help="summary CSV from script 02.")
    parser.add_argument("--spectrum-csv", type=Path, default=None, help="spectrum CSV from script 02.")

    parser.add_argument("--q0", type=float, default=None, help="Base q0 in m^-1.")
    parser.add_argument("--length-m", type=float, default=None, help="Use q0=2pi/L.")
    parser.add_argument("--n-line-um-inv", type=float, default=None, help="Use q0=pi*n_line, n_line in um^-1.")

    parser.add_argument("--a-crit-m", type=float, default=None, help="Critical length. Default: r_c.")
    parser.add_argument("--q-crit", type=float, default=None, help="Critical q in m^-1. Overrides --a-crit-m.")
    parser.add_argument("--m2-line-crit", type=float, default=None, help="Optional direct M2_line critical value in m^-3.")

    parser.add_argument("--ells", type=float, nargs="+", default=None, help="Explicit ell sectors.")
    parser.add_argument("--ell-min", type=float, default=1.0)
    parser.add_argument("--ell-max", type=float, default=None)
    parser.add_argument("--ell-step", type=float, default=1.0)

    parser.add_argument("--outdir", type=Path, default=Path("sst_ffs_03_results"))
    parser.add_argument("--no-plots", action="store_true")

    args = parser.parse_args()

    v_swirl, r_c, rho_f, gamma0, source = load_sst_constants()

    summary: dict[str, str] = {}
    if args.summary_csv is not None:
        summary = read_key_value_csv(args.summary_csv)

    q0, q0_source = resolve_q0(args, summary)

    if args.q_crit is not None:
        q_crit = float(args.q_crit)
        a_crit = 1.0 / q_crit if q_crit > 0.0 else float("nan")
        crit_source = "--q-crit"
    else:
        a_crit = float(args.a_crit_m) if args.a_crit_m is not None else float(r_c)
        q_crit = 1.0 / a_crit
        crit_source = "--a-crit-m" if args.a_crit_m is not None else "r_c"

    q_arr = None
    p_arr = None
    if args.spectrum_csv is not None:
        q_arr, p_arr = load_spectrum_csv(args.spectrum_csv)

    ells = resolve_ells(args)
    rows = [
        threshold_row(
            ell=e,
            q0=q0,
            v_swirl=v_swirl,
            q_crit=q_crit,
            m2_line_crit=args.m2_line_crit,
            q=q_arr,
            p=p_arr,
        )
        for e in ells
    ]

    ell_crit = math.sqrt(3.0) * q_crit / q0 if q0 > 0.0 else float("nan")
    n_line = q0 / math.pi

    args.outdir.mkdir(parents=True, exist_ok=True)
    scan_csv = args.outdir / "sst_ffs_03_attachment_scan.csv"
    write_scan_csv(scan_csv, rows)

    meta = {
        "constants_source": source,
        "v_swirl_m_s": v_swirl,
        "r_c_m": r_c,
        "rho_f_kg_m3": rho_f,
        "gamma0_m2_s": gamma0,
        "q0_m_inv": q0,
        "q0_source": q0_source,
        "n_line_m_inv": n_line,
        "a_crit_m": a_crit,
        "q_crit_m_inv": q_crit,
        "critical_source": crit_source,
        "ell_crit_B_equals_1": ell_crit,
        "summary_csv": str(args.summary_csv) if args.summary_csv else "",
        "spectrum_csv": str(args.spectrum_csv) if args.spectrum_csv else "",
        "m2_line_crit_m_inv3": args.m2_line_crit if args.m2_line_crit else "",
    }
    write_meta(args.outdir / "sst_ffs_03_metadata.txt", meta)

    if not args.no_plots:
        save_barrier_plot(args.outdir / "sst_ffs_03_barrier.png", rows)
        save_power_plot(args.outdir / "sst_ffs_03_contained_power.png", rows)

    print(f"SST constants source : {source}")
    print(f"q0                  : {q0:.8e} m^-1 ({q0_source})")
    print(f"N_line              : {n_line:.8e} m^-1")
    print(f"a_crit              : {a_crit:.8e} m ({crit_source})")
    print(f"q_crit              : {q_crit:.8e} m^-1")
    print(f"ell_crit(B=1)       : {ell_crit:.8f}")
    print()
    print("ell | B_ell | class | q_edge [m^-1] | f_edge [Hz] | x1 [m] | power<=edge")
    for r in rows:
        print(
            f"{r.ell:>6.2f} | {r.barrier_qcrit:>10.6e} | "
            f"{r.classification:>10s} | {r.q_edge_m_inv:>13.6e} | "
            f"{r.f_edge_hz:>11.6e} | {r.x1_m:>11.6e} | "
            f"{r.spectral_power_fraction:>10.6f}"
        )

    print()
    print(f"Wrote: {scan_csv}")
    print(f"Wrote outputs to: {args.outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
