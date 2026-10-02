
from __future__ import annotations
import sys, math, json
from .common import read_csv, load_json, dump_json, cv, mean, relerr, linreg_log

FORBIDDEN_TARGET_FIELDS = {"h","hbar","planck","target_action"}

def main(blind_csv, config_json, out_json):
    cfg=load_json(config_json)["action"]
    rows=read_csv(blind_csv)
    if len(rows) < cfg["min_observations"]:
        raise SystemExit(f"need at least {cfg['min_observations']} observations")
    for r in rows:
        bad=FORBIDDEN_TARGET_FIELDS.intersection(k.lower() for k in r.keys())
        if bad:
            raise SystemExit(f"blind input leaks target fields: {sorted(bad)}")

    vals_h=[]; vals_hbar=[]; freqs=[]; dEs=[]; omega_err=[]
    records=[]
    for r in rows:
        f=float(r["frequency_Hz"])
        omega=float(r.get("omega_rad_s") or (2*math.pi*f))
        dE=float(r["delta_E_J"])
        if f<=0 or omega<=0 or dE<=0:
            raise SystemExit("frequency, omega, and delta_E must be positive")
        Jh=dE/f
        Jhb=dE/omega
        err=relerr(omega,2*math.pi*f)
        vals_h.append(Jh); vals_hbar.append(Jhb)
        freqs.append(f); dEs.append(dE); omega_err.append(err)
        records.append({
            "opaque_id":r["opaque_id"],
            "J_f_DeltaE_over_f_J_s":Jh,
            "J_omega_DeltaE_over_omega_J_s":Jhb,
            "omega_2pi_f_rel_error":err
        })

    slope,_=linreg_log(freqs,dEs)
    gates={
        "U1_omega_equals_2pi_f": max(omega_err) <= cfg["omega_consistency_rel_tol"],
        "U2_action_universality_cv": cv(vals_h) <= cfg["universality_cv_max"],
        "U3_DeltaE_proportional_frequency": abs(slope-1.0) <= cfg["log_slope_tol"]
    }
    result={
        "format":"SST-WP-BLIND-ACTION-ANALYSIS-1.0",
        "n":len(rows),
        "target_constants_read":False,
        "summary":{
            "medianish_mean_DeltaE_over_f_J_s":mean(vals_h),
            "cv_DeltaE_over_f":cv(vals_h),
            "mean_DeltaE_over_omega_J_s":mean(vals_hbar),
            "cv_DeltaE_over_omega":cv(vals_hbar),
            "loglog_slope_DeltaE_vs_f":slope,
            "max_omega_2pi_f_rel_error":max(omega_err)
        },
        "gates":gates,
        "blind_pass":all(gates.values()),
        "records":records
    }
    dump_json(out_json,result)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    if len(sys.argv)!=4:
        raise SystemExit("usage: python -m sst_wp.action_analyze BLIND.csv config.json OUT.json")
    main(*sys.argv[1:])
