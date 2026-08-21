from __future__ import annotations
from pathlib import Path
from .utils import load_json, save_json, sha256_file


def unblind(outdir, target_path, config_path):
    outdir=Path(outdir)
    blind_path=outdir/"blind_results.json"; lock_path=outdir/"blind_lock.json"
    if not lock_path.exists(): raise RuntimeError("Refusing to unblind: blind_lock.json is missing.")
    lock=load_json(lock_path)
    if sha256_file(blind_path)!=lock["sha256"]: raise RuntimeError("Refusing to unblind: blind_results.json changed after freeze.")
    blind=load_json(blind_path); target=load_json(target_path); cfg=load_json(config_path)
    v=float(target["value_m_s"]); pooled=blind.get("pooled_speed")
    if pooled is None:
        result={"verdict":"INSUFFICIENT_DATA","target_m_s":v,"blind_verdict":blind["blind_verdict"]}
    else:
        est=float(pooled["estimate_m_s"]); lo,hi=map(float,pooled["ci95_m_s"])
        err=(est-v)/v; ratio=est/v; m=cfg["unblind"]["equivalence_margin_fraction"]
        lower=v*(1-m); upper=v*(1+m)
        inside=(lo>=lower and hi<=upper)
        outside=(hi<lower or lo>upper)
        blind_ok=blind["blind_verdict"]=="BLIND_CANDIDATE_LOCKED"
        strong_aux=(blind["cross_sample"].get("resolution_gate") is True and blind["cross_sample"].get("family_speed_gate") is not False)
        if not blind_ok:
            verdict="FALSIFIED_BEFORE_TARGET_COMPARISON"
        elif outside:
            verdict="FALSIFIED_TARGET_SPEED"
        elif inside and strong_aux:
            verdict="SURVIVES_STRONG_EQUIVALENCE_GATE"
        elif inside:
            verdict="CONSISTENT_WITH_TARGET_BUT_AUXILIARY_GATES_INCOMPLETE"
        else:
            verdict="CONSISTENT_BUT_NOT_EQUIVALENT"
        sens=[]
        for mm in cfg["unblind"]["sensitivity_margins_fraction"]:
            sens.append({"margin_fraction":mm,"ci_fully_inside":bool(lo>=v*(1-mm) and hi<=v*(1+mm))})
        result={"verdict":verdict,"blind_verdict":blind["blind_verdict"],"estimate_m_s":est,"ci95_m_s":[lo,hi],"target_m_s":v,
                "estimate_over_target":ratio,"fractional_error":err,"percent_error":100*err,"equivalence_margin_fraction":m,"sensitivity":sens,
                "note":"Survival is not confirmation; it means the pre-registered gates did not falsify the target speed."}
    save_json(outdir/"unblind_results.json",result)
    return result
