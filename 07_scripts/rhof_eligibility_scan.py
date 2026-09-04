#!/usr/bin/env python3
"""
rhof_eligibility_scan.py  --  v0.1

Triage every zip in Restore_Archives/ against the canon's own rho_f
scaling-audit classes (research track, subsec:rt_rhof_scaling_audit_v0832)
and the four promotion gates (subsec preceding it).

The question this answers is NOT "which pack derives rho_f".  It is:
"which packs are even ELIGIBLE to, i.e. produce a class-C or class-Q
observable without touching the legacy reference normalization."

Class recap (canon):
  A  rho_eff cancels from a dimensionless/acceleration observable  -> ineligible
  B  absorbed by a field or constitutive normalization             -> ineligible
  C  absolute pressure / force / energy / mass / impedance changes -> ELIGIBLE
  Q  absolute action / fluctuation / thermal / correlation scale   -> ELIGIBLE
  X  legacy number, unit error, invalid provenance                 -> disqualified

Gate 1 of the promotion rule is mechanical and is what this script
enforces: the pack must not use rhoRef, phi_dyn_ref, or ell_rho_eq as a
fitted input.  Any literal occurrence of 7.0e-7 / 6.97e-7 / 6.98e-7 /
5.7229e-26 / 5.8897 in a numeric context is a disqualifier.

Usage:
    python rhof_eligibility_scan.py Restore_Archives/ -o rhof_triage.csv
    python rhof_eligibility_scan.py Restore_Archives/ --verbose

No extraction: members are read from the zip directly.
"""

import argparse
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

TEXT_EXT = {".py", ".md", ".tex", ".txt", ".json", ".yaml", ".yml",
            ".csv", ".cpp", ".h", ".hpp", ".ipynb", ".m", ".jl"}
MAX_MEMBER_BYTES = 2_000_000
MAX_MEMBERS = 400

# ---------------------------------------------------------------- patterns

# X: legacy reference normalization used as an input  -> disqualifies gate 1
PAT_LEGACY = re.compile(
    r"(?<![\d.])(?:7\.0+(?:e|E|\*10\^|\\times10\^\{)-?0*7"
    r"|6\.9[78]\d*(?:e|E)-0*7"
    r"|6\.839859(?:e|E)-0*7"
    r"|5\.7229\d*(?:e|E)-0*26"
    r"|5\.8897)"
)
PAT_LEGACY_SYM = re.compile(r"\b(rhoRef|rho_ref|RHO_REF|phi_dyn_ref|ell_rho_eq|rho_f_legacy)\b")

# C: absolute dimensionful outputs
PAT_C = re.compile(
    r"\b(pressure|pascal|\bPa\b|stress|traction|force|newton|\bN/m\b|tension"
    r"|impedance|acoustic_impedance|mechanical_impedance"
    r"|energy_density|J/m\^?3|kg/m\^?3|kg\s*m\^?-3|mass_density|areal_density"
    r"|surface_density|line_density)\b", re.I)

# Q: absolute action / fluctuation / thermal / correlation normalization
PAT_Q = re.compile(
    r"\b(zero[_-]?point|vacuum_fluctuation|thermal_noise|kBT|k_B\s*T"
    r"|action_scale|quantum_of_circulation|shot_noise"
    r"|correlation_amplitude|structure_factor|spectral_density)\b", re.I)

# A/B: dimensionless-only or normalization-absorbed outputs
PAT_AB = re.compile(
    r"\b(dimensionless|ratio|alpha_inv|alpha_inverse|fine_structure"
    r"|ropelength|writhe|linking|helicity_normal|phase|winding"
    r"|rotation_curve|dispersion|polarization|refractive|visibility"
    r"|beta_Q|relative_entropy|monodromy|geodesic)\b", re.I)

# circular chain: quantities that already carry m_e / alpha
PAT_CHAIN = re.compile(
    r"\b(m_e|electron_mass|alpha\b|fine_structure|hbar|r_c\b|rc\b"
    r"|v_swirl|vchar|rho_core|Gamma_0|omega_c|CODATA|scipy\.constants)\b")


def classify(text):
    return {
        "legacy": len(PAT_LEGACY.findall(text)) + len(PAT_LEGACY_SYM.findall(text)),
        "C": len(PAT_C.findall(text)),
        "Q": len(PAT_Q.findall(text)),
        "AB": len(PAT_AB.findall(text)),
        "chain": len(PAT_CHAIN.findall(text)),
    }


def scan_zip(path):
    tally = {"legacy": 0, "C": 0, "Q": 0, "AB": 0, "chain": 0}
    n_text = 0
    try:
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist()[:MAX_MEMBERS]:
                if info.is_dir() or info.file_size > MAX_MEMBER_BYTES:
                    continue
                if Path(info.filename).suffix.lower() not in TEXT_EXT:
                    continue
                try:
                    raw = zf.read(info)
                except Exception:
                    continue
                text = raw.decode("utf-8", errors="ignore")
                n_text += 1
                for k, v in classify(text).items():
                    tally[k] += v
    except zipfile.BadZipFile:
        return None, 0
    return tally, n_text


def verdict(t):
    """Return (class, eligible, reason)."""
    if t["legacy"] > 0:
        return "X", False, f"uses legacy reference normalization ({t['legacy']} hits) -> gate 1 fails"
    cq = t["C"] + t["Q"]
    if cq == 0:
        return "A/B", False, "no absolute dimensionful or action-scale observable found"
    if t["AB"] > 6 * cq:
        return "A/B", False, f"dominated by dimensionless observables (AB={t['AB']} vs CQ={cq})"
    cls = "C" if t["C"] >= t["Q"] else "Q"
    warn = " [WARN: heavy calibrated-chain dependence]" if t["chain"] > 3 * cq else ""
    return cls, True, f"absolute observable present (C={t['C']}, Q={t['Q']}){warn}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=Path("rhof_triage.csv"))
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    zips = sorted(args.root.rglob("*.zip"))
    if not zips:
        sys.exit(f"no zips under {args.root}")

    rows = []
    for p in zips:
        t, n = scan_zip(p)
        if t is None:
            rows.append(dict(theme=p.parent.name, zip=p.name, cls="ERR",
                             eligible=False, reason="bad zip", **dict.fromkeys(
                                 ["legacy", "C", "Q", "AB", "chain"], 0), n_text=0))
            continue
        cls, ok, why = verdict(t)
        rows.append(dict(theme=p.parent.name, zip=p.name, cls=cls,
                         eligible=ok, reason=why, n_text=n, **t))
        if args.verbose:
            mark = "ELIGIBLE" if ok else "        "
            print(f"{mark}  [{cls:4s}] {p.parent.name}/{p.name}: {why}")

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    elig = [r for r in rows if r["eligible"]]
    print(f"\nscanned {len(rows)} zips -> {args.out}")
    print(f"eligible (class C or Q, gate 1 clean): {len(elig)}")
    by_theme = {}
    for r in elig:
        by_theme.setdefault(r["theme"], 0)
        by_theme[r["theme"]] += 1
    for k in sorted(by_theme, key=lambda k: -by_theme[k]):
        print(f"   {k:18s} {by_theme[k]}")
    print("\nNOTE: eligibility is necessary, not sufficient. Gates 2-4 "
          "(RVE/discretization/BC convergence, twist-bend distinction and "
          "units, one out-of-sample prediction) must still be closed by hand.")


if __name__ == "__main__":
    main()
