from __future__ import annotations
import argparse, json, hashlib, shutil
from pathlib import Path
import numpy as np
from .common import load_json, dump_json, sha256_file, relerr, read_csv
from .reveal_normalization import dimensional_action_scale
from . import reveal_constants as C

def _load_normalization(path):
    if not path:
        return None
    n = load_json(path)
    required = ["rho_kg_m3", "Gamma_m2_s", "L_m"]
    missing = [k for k in required if k not in n or n[k] is None]
    if missing:
        raise SystemExit(f"Normalization file missing required values: {missing}")
    n["J0_J_s"] = dimensional_action_scale(
        n["rho_kg_m3"], n["Gamma_m2_s"], n["L_m"]
    )
    return n

def main():
    p = argparse.ArgumentParser()
    p.add_argument("blind_analysis")
    p.add_argument("seal")
    p.add_argument("blind_csv")
    p.add_argument("--private-dir", default="private_reveal_keys")
    p.add_argument("--normalization", default=None,
                   help="Reveal-only independent SI normalization JSON.")
    p.add_argument("--out", required=True)
    a = p.parse_args()

    ana = load_json(a.blind_analysis)
    seal = load_json(a.seal)
    kp = Path(a.private_dir) / seal["private_key_name"]
    key = load_json(kp)

    commit = hashlib.sha256(
        json.dumps(key["mapping"], sort_keys=True).encode()
    ).hexdigest()
    integrity = (
        commit == seal["private_key_commitment_sha256"]
        == key["commitment_sha256"]
        and sha256_file(a.blind_csv) == seal["blind_sha256"]
    )

    rows = read_csv(a.blind_csv)
    jf_hat = [
        float(r["delta_E_hat"]) / float(r["frequency_hat"])
        for r in rows
        if float(r["delta_E_hat"]) > 0 and float(r["frequency_hat"]) > 0
    ]
    jw_hat = [
        float(r["delta_E_hat"]) / float(r["omega_hat"])
        for r in rows
        if float(r["delta_E_hat"]) > 0 and float(r["omega_hat"]) > 0
    ]
    Jf_hat = float(np.median(jf_hat)) if jf_hat else None
    Jw_hat = float(np.median(jw_hat)) if jw_hat else None

    norm = _load_normalization(a.normalization)
    absolute = {
        "status": "INDETERMINATE_NO_INDEPENDENT_SI_NORMALIZATION",
        "normalization_supplied": norm is not None,
        "independent_of_Planck_chain": None,
    }
    absolute_pass = False

    if norm is not None:
        independent = bool(norm.get("independent_of_Planck_chain", False))
        J0 = float(norm["J0_J_s"])
        Jf = J0 * Jf_hat if Jf_hat is not None else None
        Jw = J0 * Jw_hat if Jw_hat is not None else None
        eh = relerr(Jf, C.h) if Jf is not None else None
        ehw = relerr(Jw, C.hbar) if Jw is not None else None
        absolute = {
            "status":
                "ELIGIBLE_INDEPENDENT_NORMALIZATION"
                if independent
                else "CONTAMINATED_OR_UNPROVEN_NORMALIZATION",
            "normalization_supplied": True,
            "independent_of_Planck_chain": independent,
            "provenance_note": norm.get("provenance_note", ""),
            "rho_kg_m3": norm["rho_kg_m3"],
            "Gamma_m2_s": norm["Gamma_m2_s"],
            "L_m": norm["L_m"],
            "J0_J_s": J0,
            "physical_DeltaE_over_f_J_s": Jf,
            "physical_DeltaE_over_omega_J_s": Jw,
            "h_J_s": C.h,
            "hbar_J_s": C.hbar,
            "relative_error_to_h": eh,
            "relative_error_to_hbar": ehw,
        }
        tol = float(norm.get("target_relative_tolerance", 0.05))
        absolute_pass = bool(
            independent
            and eh is not None and ehw is not None
            and eh <= tol and ehw <= tol
        )

    out = {
        "format": "SST-WP-REVEAL-2.1",
        "integrity_ok": integrity,
        "blind_pass": ana["blind_pass"],
        "dimensionless_discovery": {
            "median_Jf_hat": Jf_hat,
            "median_Jomega_hat": Jw_hat,
            "claim":
                "Internal dimensionless universal-action candidate only; "
                "no absolute Planck normalization is implied.",
        },
        "absolute_normalization_audit": absolute,
        "UA2_absolute_Planck_normalization_pass": absolute_pass,
        "final_dimensionless_candidate_pass":
            bool(integrity and ana["blind_pass"]),
        "final_absolute_Planck_pass":
            bool(integrity and ana["blind_pass"] and absolute_pass),
        "warning":
            "A canonical or otherwise Planck-contaminated normalization cannot "
            "turn a dimensionless candidate into an independent prediction of h or hbar.",
        "reveal_mapping": key["mapping"],
    }

    outdir = Path(a.out).parent
    if key.get("private_raw_name") and (
        Path(a.private_dir) / key["private_raw_name"]
    ).exists():
        shutil.copy2(
            Path(a.private_dir) / key["private_raw_name"],
            outdir / "REVEALED_RAW_OBSERVATIONS.csv",
        )
    if key.get("private_campaign_name") and (
        Path(a.private_dir) / key["private_campaign_name"]
    ).exists():
        shutil.copy2(
            Path(a.private_dir) / key["private_campaign_name"],
            outdir / "REVEALED_CAMPAIGN_PRIVATE.json",
        )
    dump_json(a.out, out)
    print(json.dumps(
        {k: v for k, v in out.items() if k != "reveal_mapping"},
        indent=2
    ))

if __name__ == "__main__":
    main()
