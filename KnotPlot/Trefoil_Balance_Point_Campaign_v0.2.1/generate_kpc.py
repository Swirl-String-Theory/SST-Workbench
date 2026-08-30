from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())

def v(x):
    if isinstance(x,str): return x
    if isinstance(x,bool): return "true" if x else "false"
    return f"{x:.15g}"

def cp(rid,it):
    o="__BUNDLE_ROOT__/out"; tag=f"i{it:05d}"
    return ["centre","safe","dowker","lnknum","length","distance","angle","acn",
            f"save {o}/{rid}_{tag}.k float",f"coords {o}/{rid}_{tag}.txt"]

def runtime(s,refine=True):
    x=[]
    if refine:x+=["refine nbeads 300"]
    x+=["mode cb","centre","fitto mindist 1.05","collision fast","energy model MD"]
    for k,val in D["frozen_non_qhp_baseline"].items(): x.append(f"{k} = {v(val)}")
    x += [f"charge = {v(s['charge'])}",f"hooke = {v(s['hooke'])}",f"power = {v(s['power'])}"]
    return x

def standard(s):
    rid=f"K31__{s['id']}"
    lines=["% v0.2.1 STANDARD",f"% t={s['t']}","reset all","load 3.1",*runtime(s,True),*cp(rid,0)]
    last=0
    for it in D["standard"]["checkpoints"][1:]:
        lines += [f"ago {it-last}",*cp(rid,it)]; last=it
    lines+=["stop"]
    return rid,"\n".join(lines)+"\n"

def extended(s):
    rid=f"K31__{s['id']}"
    lines=["% v0.2.1 EXTENDED",f"% t={s['t']}","reset all",
           f"load __BUNDLE_ROOT__/out/{rid}_i30000.k",*runtime(s,False)]
    last=30000
    for it in D["extended"]["additional_checkpoints"]:
        lines += [f"ago {it-last}",*cp(rid,it)]; last=it
    lines+=["stop"]
    return rid,"\n".join(lines)+"\n"

def main():
    for n in ("kpc_standard","kpc_extended"):
        p=ROOT/n
        if p.exists(): shutil.rmtree(p)
        p.mkdir()
    idx=[]
    for s in D["settings"]:
        rid,a=standard(s); _,b=extended(s)
        (ROOT/"kpc_standard"/f"{rid}.kpc").write_text(a,encoding="utf-8",newline="\n")
        (ROOT/"kpc_extended"/f"{rid}.kpc").write_text(b,encoding="utf-8",newline="\n")
        idx.append({"run_id":rid,**s})
    for n in ("kpc_standard","kpc_extended"):
        (ROOT/n/"index.json").write_text(json.dumps(idx,indent=2)+"\n")
    print("GENERATED 20 standard scripts to i30000")
    print("GENERATED 20 continuation scripts i30000 -> i60000")
if __name__=="__main__":main()
