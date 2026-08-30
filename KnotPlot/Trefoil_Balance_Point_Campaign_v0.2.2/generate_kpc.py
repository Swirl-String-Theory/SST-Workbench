from __future__ import annotations
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def v(x):
    if isinstance(x,str): return x
    if isinstance(x,bool): return "true" if x else "false"
    return f"{x:.15g}"

def restore(s):
    lines=["mode cb","collision fast","energy model MD"]
    for k,x in D["frozen_non_qhp_baseline"].items():
        lines.append(f"{k} = {v(x)}")
    lines += [
        f"charge = {v(s['charge'])}",
        f"hooke = {v(s['hooke'])}",
        f"power = {v(s['power'])}",
    ]
    return lines

def probe(s):
    rid=f"K31__{s['id']}"
    src=f"__BUNDLE_ROOT__/out/{rid}_i60000.k"
    chk=f"__BUNDLE_ROOT__/analysis/resume_checks/{rid}_i60000_reload.txt"
    lines=[
        "% Trefoil Balance v0.2.2 METRIC-NEUTRAL 60k reload probe",
        f"% frozen t={s['t']}",
        "reset all",f"load {src}",*restore(s),
        f"coords {chk}",
        "stop",
    ]
    return rid,"\n".join(lines)+"\n"

def checkpoint(rid,it):
    o="__BUNDLE_ROOT__/out"
    tag=f"i{it:05d}"
    return [
        "centre","safe","dowker","lnknum","length","distance","angle","acn",
        f"save {o}/{rid}_{tag}.k float",
        f"coords {o}/{rid}_{tag}.txt",
    ]

def continuation(s):
    rid=f"K31__{s['id']}"
    src=f"__BUNDLE_ROOT__/out/{rid}_i60000.k"
    lines=[
        "% Trefoil Balance v0.2.2 METRIC-NEUTRAL 60k->100k",
        f"% frozen t={s['t']}",
        "reset all",f"load {src}",*restore(s),
    ]
    # Absolutely no centre/refine/fitto before the first resumed ago.
    last=60000
    for it in D["continuation"]["additional_checkpoints"]:
        lines += [f"ago {it-last}",*checkpoint(rid,it)]
        last=it
    lines.append("stop")
    return rid,"\n".join(lines)+"\n"

def main():
    pdir=ROOT/"kpc_probe";cdir=ROOT/"kpc_continuation"
    pdir.mkdir(exist_ok=True);cdir.mkdir(exist_ok=True)
    pi=[];ci=[]
    expected_p=set();expected_c=set()
    for s in D["settings"]:
        rid,txt=probe(s)
        p=pdir/f"{rid}.kpc";p.write_text(txt,encoding="utf-8",newline="\n")
        expected_p.add(p.name);pi.append({"run_id":rid,**s})
        rid,txt=continuation(s)
        p=cdir/f"{rid}.kpc";p.write_text(txt,encoding="utf-8",newline="\n")
        expected_c.add(p.name);ci.append({"run_id":rid,**s})
    for folder,expected in [(pdir,expected_p),(cdir,expected_c)]:
        for p in folder.glob("*.kpc"):
            if p.name not in expected:
                try:p.unlink()
                except PermissionError: print("WARNING stale locked:",p)
    (pdir/"index.json").write_text(json.dumps(pi,indent=2)+"\n",encoding="utf-8")
    (cdir/"index.json").write_text(json.dumps(ci,indent=2)+"\n",encoding="utf-8")
    print("GENERATE PASS: 20 probes + 20 metric-neutral continuations")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
