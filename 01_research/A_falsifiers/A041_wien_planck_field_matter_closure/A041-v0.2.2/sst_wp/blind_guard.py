from __future__ import annotations
import json, re
from pathlib import Path

# Files that participate in the pre-reveal scientific path.
BLIND_MODULES = [
    "sst_wp/campaign.py",
    "sst_wp/energy.py",
    "sst_wp/action_prepare.py",
    "sst_wp/action_analyze.py",
    "sst_wp/dynamics.py",
    "sst_wp/kernels.py",
    "sst_wp/modal.py",
    "sst_wp/perturb.py",
    "sst_wp/geometry.py",
    "sst_wp/relative_equilibrium.py",
    "sst_wp/common.py",
]

# Exact canonical numerical fingerprints forbidden in blind scientific source/config/payload.
FORBIDDEN_NUMERIC_FINGERPRINTS = [
    "1.09384563e6",
    "1.40897017e-15",
    "3.8934358266918687e18",
    "7.0e-7",
    "29.053507",
    "3.02563e43",
    "6.62607015e-34",
    "1.054571817",
]

# Symbolic/provenance terms forbidden in blind payloads and configs.
FORBIDDEN_PAYLOAD_TERMS = [
    "v_swirl",
    "rho_core",
    "rho_f",
    "f_swirl_max",
    "f_gr_max",
    "gamma_c",
    "planck_target",
    "target_action",
    "hbar",
    "delta_e_j",
    "frequency_hz",
    "omega_rad_s",
    "l_phys_m",
    "gamma_phys",
    "rho_energy",
]

def scan_blind_payload_leak(obj):
    txt = json.dumps(obj, sort_keys=True).lower()
    bad = []
    for token in FORBIDDEN_NUMERIC_FINGERPRINTS:
        if token.lower() in txt:
            bad.append(token)
    for token in FORBIDDEN_PAYLOAD_TERMS:
        if token in txt:
            bad.append(token)
    return sorted(set(bad))

def assert_blind_config_clean(cfg):
    bad = scan_blind_payload_leak(cfg)
    if bad:
        raise RuntimeError(f"Blind config contains forbidden SST/SI/target material: {bad}")
    if float(cfg.get("gamma_dimensionless", 1.0)) != 1.0:
        raise RuntimeError("Strict dimensionless blind normalization requires gamma_dimensionless=1")
    return True

def scan_blind_source(root):
    root = Path(root)
    bad = []
    forbidden_imports = [
        "reveal_constants",
        "provenance",
        "action_reveal",
    ]
    forbidden_symbols = [
        r"\bv_swirl\b",
        r"\br_c\b",
        r"\brho_core\b",
        r"\brho_f\b",
        r"\bF_swirl_max\b",
        r"\bF_gr_max\b",
        r"\bGamma_c\b",
        r"\bhbar\b",
    ]
    for rel in BLIND_MODULES:
        p = root / rel
        if not p.exists():
            bad.append(f"{rel}:MISSING")
            continue
        txt = p.read_text(encoding="utf-8")
        low = txt.lower()
        for token in forbidden_imports:
            if token.lower() in low:
                bad.append(f"{rel}:import/token:{token}")
        for token in FORBIDDEN_NUMERIC_FINGERPRINTS:
            if token.lower() in low:
                bad.append(f"{rel}:numeric:{token}")
        for pat in forbidden_symbols:
            if re.search(pat, txt):
                bad.append(f"{rel}:symbol:{pat}")
    return bad

def assert_blind_code_clean(root):
    bad = scan_blind_source(root)
    if bad:
        raise RuntimeError(
            "Blind scientific code contains forbidden SST/reveal material:\n"
            + "\n".join(bad)
        )
    return True

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None)
    a = p.parse_args()
    root = Path(__file__).resolve().parents[1]
    bad = scan_blind_source(root)
    result = {
        "format": "SST-WP-BLIND-GUARD-2.2",
        "blind_modules": BLIND_MODULES,
        "violations": bad,
        "pass": not bad,
    }
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not bad else 2

if __name__ == "__main__":
    raise SystemExit(main())
