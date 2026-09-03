
from __future__ import annotations
import sys, json, math
from collections import defaultdict
from .common import read_csv, load_json, dump_json, mean, cv, relerr

def main(inp_csv, config_json, out_json):
    cfg=load_json(config_json)["closure"]
    rows=read_csv(inp_csv)

    # A: Wien/Euler similarity q=a^2 omega should be invariant
    sim=[float(r["scale_a"])**2*float(r["omega_rad_s"]) for r in rows if r.get("scale_a") and r.get("omega_rad_s")]
    A = bool(sim) and cv(sim)<=cfg["similarity_cv_max"]

    # B1 energy/inertial mass equivalence
    masserrs=[relerr(float(r["M_E_kg"]),float(r["M_I_kg"])) for r in rows if r.get("M_E_kg") and r.get("M_I_kg")]
    B1=bool(masserrs) and max(masserrs)<=cfg["mass_equivalence_rel_tol"]

    # B2 pressure-monopole / inertial-mass universality; no imported gravitational target
    grav=[float(r["C_p"])/float(r["M_I_kg"]) for r in rows if r.get("C_p") and r.get("M_I_kg")]
    B2=bool(grav) and cv(grav)<=cfg["gravity_ratio_cv_max"]

    # D: field-matter statistical closure
    betaerrs=[relerr(float(r["beta_knot"]),float(r["beta_fluid"])) for r in rows if r.get("beta_knot") and r.get("beta_fluid")]
    D1=bool(betaerrs) and max(betaerrs)<=cfg["beta_rel_tol"]
    drifts=[abs(float(r["energy_drift_rel"])) for r in rows if r.get("energy_drift_rel")]
    D2=bool(drifts) and max(drifts)<=cfg["energy_drift_rel_max"]

    gates={
        "A_Wien_Euler_similarity":A,
        "B1_energy_inertial_mass_closure":B1,
        "B2_pressure_monopole_mass_universality":B2,
        "D1_beta_knot_fluid_equilibration":D1,
        "D2_total_energy_conservation":D2
    }
    out={
        "format":"SST-WP-FIELD-MATTER-CLOSURE-1.0",
        "n":len(rows),
        "metrics":{
            "similarity_cv":cv(sim) if sim else None,
            "max_mass_relative_error":max(masserrs) if masserrs else None,
            "Cp_over_MI_cv":cv(grav) if grav else None,
            "max_beta_relative_error":max(betaerrs) if betaerrs else None,
            "max_energy_drift_rel":max(drifts) if drifts else None
        },
        "gates":gates,
        "pass":all(gates.values())
    }
    dump_json(out_json,out)
    print(json.dumps(out,indent=2))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m sst_wp.closure_analyze INPUT.csv config.json OUT.json")
    main(*sys.argv[1:])
