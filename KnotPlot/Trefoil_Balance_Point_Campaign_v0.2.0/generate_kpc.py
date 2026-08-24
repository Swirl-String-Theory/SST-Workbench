from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def vv(x):
    if isinstance(x,str): return x
    if isinstance(x,bool): return "true" if x else "false"
    return f"{x:.15g}"

def checkpoint(rid,it):
    tag=f"i{it:05d}"
    out="__BUNDLE_ROOT__/out"
    return [
        f"echo CHECKPOINT {rid}_{tag}",
        "centre","safe","dowker","lnknum","length","distance","angle","acn",
        f"save {out}/{rid}_{tag}.k float",
        f"coords {out}/{rid}_{tag}.txt",
    ]

def make(s):
    rid=f"K31__{s['id']}"
    lines=[
        "% AUTO-GENERATED Trefoil Balance Point Campaign v0.2.0",
        f"% run_id={rid}",
        f"% lane={s['lane']}",
        f"% q={s['charge']:.15g} h={s['hooke']:.15g} p={s['power']:.15g}",
        "reset all","load 3.1","refine nbeads 300","mode cb","centre",
        "fitto mindist 1.05","collision fast","energy model MD",
    ]
    for k,x in D["frozen_non_qhp_baseline"].items():
        lines.append(f"{k} = {vv(x)}")
    lines += [
        f"charge = {vv(s['charge'])}",
        f"hooke = {vv(s['hooke'])}",
        f"power = {vv(s['power'])}",
        *checkpoint(rid,0),
    ]
    last=0
    for it in D["checkpoints"][1:]:
        lines.append(f"ago {it-last}")
        lines.extend(checkpoint(rid,it))
        last=it
    lines.append("stop")
    return rid,"\n".join(lines)+"\n"

def main():
    kd=ROOT/"kpc"
    if kd.exists(): shutil.rmtree(kd)
    kd.mkdir()
    idx=[]
    for s in D["settings"]:
        rid,text=make(s)
        p=kd/f"{rid}.kpc";p.write_text(text,encoding="utf-8",newline="\n")
        idx.append({"run_id":rid,**{k:s[k] for k in ("id","lane","scan_coordinate","scan_value","charge","hooke","power")}})
    (kd/"index.json").write_text(json.dumps(idx,indent=2)+"\n",encoding="utf-8")
    print(f"GENERATED {len(idx)} K31 zero-bracket scripts")
    print("  full balance ray:",sum(x["lane"]=="full_balance_ray_extended" for x in idx))
    print("  hooke bracket   :",sum(x["lane"]=="hooke_dominant_bracket" for x in idx))
    return 0
if __name__=="__main__": raise SystemExit(main())
