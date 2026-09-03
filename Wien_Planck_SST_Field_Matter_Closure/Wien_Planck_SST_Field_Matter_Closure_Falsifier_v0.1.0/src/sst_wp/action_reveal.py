
from __future__ import annotations
import sys, math, json
from .common import load_json, dump_json, relerr

H = 6.62607015e-34
HBAR = H/(2*math.pi)

def main(analysis_json, key_json, config_json, out_json):
    a=load_json(analysis_json)
    key=load_json(key_json)
    cfg=load_json(config_json)["action"]
    Jh=a["summary"]["medianish_mean_DeltaE_over_f_J_s"]
    Jhb=a["summary"]["mean_DeltaE_over_omega_J_s"]
    eh=relerr(Jh,H)
    ehb=relerr(Jhb,HBAR)
    result={
        "format":"SST-WP-ACTION-REVEAL-1.0",
        "blind_pass":a["blind_pass"],
        "target_comparison":{
            "measured_DeltaE_over_f_J_s":Jh,
            "h_J_s":H,
            "relative_error_to_h":eh,
            "measured_DeltaE_over_omega_J_s":Jhb,
            "hbar_J_s":HBAR,
            "relative_error_to_hbar":ehb
        },
        "gates":{
            **a["gates"],
            "U4_reveal_matches_h_and_hbar": max(eh,ehb) <= cfg["target_rel_tol"]
        },
        "final_pass": a["blind_pass"] and max(eh,ehb)<=cfg["target_rel_tol"],
        "hidden_fields":key["hidden_fields"],
        "source_sha256":key["source_sha256"]
    }
    dump_json(out_json,result)
    print(json.dumps(result,indent=2))

if __name__=="__main__":
    if len(sys.argv)!=5:
        raise SystemExit("usage: python -m sst_wp.action_reveal ANALYSIS.json KEY.json config.json OUT.json")
    main(*sys.argv[1:])
