from __future__ import annotations
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def v(x):
    if isinstance(x,str): return x
    if isinstance(x,bool): return "true" if x else "false"
    return f"{x:.15g}"

def checkpoint(rid,it):
    o="__BUNDLE_ROOT__/out"
    tag=f"i{it:05d}"
    return [
        "centre","safe","dowker","lnknum","length","distance","angle","acn",
        f"save {o}/{rid}_{tag}.k float",
        f"coords {o}/{rid}_{tag}.txt",
    ]

def script(s):
    rid=f"K31__{s['id']}"
    # IMPORTANT: after loading the saved state, do not run fitto/refine/centre.
    # centre at later checkpoints is translation-only and matches the original
    # checkpoint protocol; the state loaded at i30000 was already centred.
    lines=[
        "% v0.2.1 METRIC-NEUTRAL EXTENDED",
        f"% t={s['t']}",
        "reset all",
        f"load __BUNDLE_ROOT__/out/{rid}_i30000.k",
        "mode cb",
        "collision fast",
        "energy model MD",
    ]
    for k,val in D["frozen_non_qhp_baseline"].items():
        lines.append(f"{k} = {v(val)}")
    lines += [
        f"charge = {v(s['charge'])}",
        f"hooke = {v(s['hooke'])}",
        f"power = {v(s['power'])}",
        # Snapshot immediately after reload + non-geometric parameter restore.
        f"coords __BUNDLE_ROOT__/analysis/resume_checks/{rid}_i30000_resumecheck.txt",
    ]
    last=30000
    for it in D["extended"]["additional_checkpoints"]:
        lines += [f"ago {it-last}",*checkpoint(rid,it)]
        last=it
    lines.append("stop")
    return rid,"\n".join(lines)+"\n"

def main():
    out=ROOT/"kpc_extended"
    out.mkdir(parents=True,exist_ok=True)
    idx=[]
    expected=set()
    for s in D["settings"]:
        rid,text=script(s)
        p=out/f"{rid}.kpc"
        p.write_text(text,encoding="utf-8",newline="\n")
        expected.add(p.name)
        idx.append({"run_id":rid,**s})
    for p in out.glob("*.kpc"):
        if p.name not in expected:
            try:p.unlink()
            except PermissionError:
                print("WARNING stale locked KPC:",p)
    (out/"index.json").write_text(json.dumps(idx,indent=2)+"\n",encoding="utf-8")
    print("METRIC-NEUTRAL EXTENDED GENERATOR PASS")
    print("20 continuation scripts: i30000 -> i60000")
    print("Resume geometry transforms: fitto=OFF refine=OFF centre-at-load=OFF")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
