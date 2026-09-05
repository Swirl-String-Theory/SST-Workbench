from __future__ import annotations
from pathlib import Path
import json,shutil,re

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"matrix_design.json").read_text(encoding="utf-8"))

def val(x):
    if isinstance(x,bool): return "on" if x else "off"
    if isinstance(x,str): return x
    return f"{x:g}"

def assignments(recipe):
    # These are runtime variables and therefore MUST use `=`.
    return [
        f"close = {val(recipe['close'])}",
        f"max-dr = {val(recipe['max_dr'])}",
        f"mechforce = {val(recipe['mechforce'])}",
        f"elecforce = {val(recipe['elecforce'])}",
        f"bendforce = {val(recipe['bendforce'])}",
        f"charge = {val(recipe['charge'])}",
        f"hooke = {val(recipe['hooke'])}",
        f"power = {val(recipe['power'])}",
        f"tinc = {val(recipe['tinc'])}",
        f"bencon = {val(recipe['bencon'])}",
        f"stusplit = {val(recipe['stusplit'])}",
        f"dstep = {val(recipe['dstep'])}",
        f"bradius = {val(recipe['bradius'])}",
        f"cradius = {val(recipe['cradius'])}",
    ]

def checkpoint(cid,it):
    tag=f"i{it:05d}"
    root="__BUNDLE_ROOT__/out"
    return [
        f"echo CHECKPOINT {cid}_{tag}",
        "centre",
        "safe","dowker","lnknum",
        "length","distance","angle","acn",
        f"save {root}/{cid}_{tag}.k float",
        f"coords {root}/{cid}_{tag}.txt",
    ]

def standard_script(e):
    cid=e["candidate"]; r=e["recipe"]
    lines=[
        "% AUTO-GENERATED MultiDynamics Matrix v0.1.7",
        f"% candidate={cid}",
        "reset all","load 3.1","refine nbeads 300","mode cb",
        "centre","fitto mindist 1.05",
        f"collision {r['collision']}",
        f"energy model {r['energy_model']}",
        *assignments(r),
        *checkpoint(cid,0),
        "ago 1000",*checkpoint(cid,1000),
        "ago 3000",*checkpoint(cid,4000),
        "ago 6000",*checkpoint(cid,10000),
        "stop",
    ]
    return "\n".join(lines)+"\n"

def anneal_script(e):
    # Frozen historical schedule, now using valid assignment syntax.
    cid=e["candidate"]; r=e["recipe"]
    lines=[
        "% AUTO-GENERATED MultiDynamics Matrix v0.1.7",
        "% charge anneal schedule: 60 -> 30 -> 15 -> 7.5 -> 0",
        "reset all","load 3.1","refine nbeads 300","mode cb",
        "centre","fitto mindist 1.05",
        f"collision {r['collision']}",f"energy model {r['energy_model']}",
        *assignments(r),
        "charge = 60",
        *checkpoint("A90_anneal_q60",0),
        "ago 1000",*checkpoint("A90_anneal_q60",1000),
        "charge = 30","ago 1500",*checkpoint("A90_anneal_q30",2500),
        "charge = 15","ago 2000",*checkpoint("A90_anneal_q15",4500),
        "charge = 7.5","ago 2500",*checkpoint("A90_anneal_q7p5",7000),
        "charge = 0","ago 3000",*checkpoint("A90_anneal_q0",10000),
        "stop",
    ]
    return "\n".join(lines)+"\n"

def main():
    kd=ROOT/"kpc"
    if kd.exists(): shutil.rmtree(kd)
    kd.mkdir(parents=True)
    idx=[]
    for e in D["entries"]:
        p=kd/f"{e['candidate']}.kpc"
        txt=anneal_script(e) if e["family"]=="charge_anneal_MEB" else standard_script(e)
        p.write_text(txt,encoding="utf-8",newline="\n")
        idx.append({"candidate":e["candidate"],"family":e["family"],"script":str(p.relative_to(ROOT))})
    (kd/"index.json").write_text(json.dumps(idx,indent=2)+"\n",encoding="utf-8")
    print(f"GENERATED {len(idx)} candidate scripts")
if __name__=="__main__":
    main()
