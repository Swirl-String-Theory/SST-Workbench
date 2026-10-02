from __future__ import annotations
import hashlib, json, math
from pathlib import Path


def canonical_commit(entry: dict) -> str:
    payload="|".join([entry["name"],repr(float(entry["value"])),entry["unit"],entry["role"],repr(float(entry.get("tolerance_rel",0.0))),entry["salt"]])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_commitments(commitments_path: Path,key_path: Path):
    c=json.loads(commitments_path.read_text(encoding="utf-8")); k=json.loads(key_path.read_text(encoding="utf-8"))
    cmap={e["name"]:e["sha256"] for e in c["entries"]}; out=[]
    for e in k["entries"]:
        h=canonical_commit(e); out.append({"name":e["name"],"ok":cmap.get(e["name"])==h,"sha256":h})
    return out,k


def unblind_report(blind_report: Path,commitments: Path,key_path: Path,out_path: Path):
    checks,key=verify_commitments(commitments,key_path)
    if not all(x["ok"] for x in checks): raise ValueError("unblind key does not match preregistered commitments")
    report=json.loads(blind_report.read_text(encoding="utf-8")); entries={e["name"]:e for e in key["entries"]}; comparisons=[]
    stress=report.get("tracks",{}).get("stress")
    if stress:
        c=stress.get("metrics",{}).get("median_C_blind")
        if c is not None:
            for name in ("maxwell_uniform_vortex_C_edge","sst_bernoulli_C_edge"):
                e=entries[name]; comparisons.append({"quantity":"stress.C","target":name,"observed":c,"target_value":e["value"],"relative_difference":abs(c-e["value"])/abs(e["value"]),"role":e["role"],"status":"COMPARISON_ONLY"})
    rm=report.get("tracks",{}).get("reduced_momentum")
    if rm:
        beta=rm.get("A_over_u",{}).get("beta_blind")
        if beta is not None:
            e=entries["electron_A_over_u_m_e_over_e"]; rel=abs(beta-e["value"])/abs(e["value"]); tol=e["tolerance_rel"]
            comparisons.append({"quantity":"A_over_u","target":e["name"],"observed":beta,"target_value":e["value"],"relative_difference":rel,"tolerance_rel":tol,"role":e["role"],"status":"PASS" if rel<=tol else "FAIL"})
    out={"commitment_verification":checks,"blind_verdict":report.get("overall_status"),"comparisons":comparisons}
    out_path.write_text(json.dumps(out,indent=2),encoding="utf-8"); return out
