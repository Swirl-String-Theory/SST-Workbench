from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())

def val(v):
    if isinstance(v,str): return v
    return f"{v:.15g}"

def checkpoint(rid,it):
    tag=f"i{it:05d}"
    out="__BUNDLE_ROOT__/out"
    return [
        f"echo CHECKPOINT {rid}_{tag}",
        "centre","safe","dowker","lnknum","length","distance","angle","acn",
        f"save {out}/{rid}_{tag}.k float",
        f"coords {out}/{rid}_{tag}.txt",
    ]

def make(v,s):
    rid=f"{v['id']}__{s['id']}"
    lines=[
        "% AUTO-GENERATED Trefoil Balance Point Campaign v0.1.0",
        f"% run_id={rid}",
        "reset all",*v["construction"],
        "refine nbeads 300","mode cb","centre","fitto mindist 1.05",
        "collision fast","energy model MD",
    ]
    for k,x in D["frozen_non_qhp_baseline"].items():
        lines.append(f"{k} = {val(x)}")
    lines += [
        f"charge = {val(s['charge'])}",
        f"hooke = {val(s['hooke'])}",
        f"power = {val(s['power'])}",
        *checkpoint(rid,0),
        "ago 25",*checkpoint(rid,25),
        "ago 75",*checkpoint(rid,100),
        "ago 400",*checkpoint(rid,500),
        "ago 500",*checkpoint(rid,1000),
        "ago 3000",*checkpoint(rid,4000),
        "ago 6000",*checkpoint(rid,10000),
        "stop",
    ]
    return rid,"\n".join(lines)+"\n"

def main():
    kd=ROOT/"kpc"
    if kd.exists(): shutil.rmtree(kd)
    kd.mkdir()
    idx=[]
    for v in D["variants"]:
        for s in D["settings"]:
            rid,text=make(v,s)
            p=kd/f"{rid}.kpc"
            p.write_text(text,encoding="utf-8",newline="\n")
            idx.append({"run_id":rid,"variant":v["id"],"setting":s["id"],
                        "charge":s["charge"],"hooke":s["hooke"],"power":s["power"]})
    (kd/"index.json").write_text(json.dumps(idx,indent=2)+"\n")
    print(f"GENERATED {len(idx)} scripts = 2 variants x 10 settings")
if __name__=="__main__": main()
