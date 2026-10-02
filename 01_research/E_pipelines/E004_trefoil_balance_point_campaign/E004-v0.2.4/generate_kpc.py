from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text(encoding="utf-8"))

def v(x):
    if isinstance(x,str):return x
    if isinstance(x,bool):return "true" if x else "false"
    return f"{x:.15g}"

def restore(s):
    x=["mode cb","collision fast","energy model MD"]
    for k,val in D["frozen_non_qhp_baseline"].items():x.append(f"{k} = {v(val)}")
    x += [f"charge = {v(s['charge'])}",f"hooke = {v(s['hooke'])}",f"power = {v(s['power'])}"]
    return x

def cp(rid,it,initial=False):
    tag=f"i{it:06d}";o="__BUNDLE_ROOT__/out"
    x=[]
    # Frozen i0 is already centred. Historical runs centred at every later checkpoint.
    if not initial:x.append("centre")
    x += ["safe","dowker","lnknum","length","distance","angle","acn",
          f"save {o}/{rid}_{tag}.k float",f"coords {o}/{rid}_{tag}.txt"]
    return x

def cold(s):
    rid=f"XQHP__{s['id']}"
    lines=["% v0.2.4 COLD START from common historical i0 geometry",
           f"% t={s['t']} role={s['role']}",
           "reset all","load __BUNDLE_ROOT__/reference/FROZEN_K31_i00000.txt",*restore(s),*cp(rid,0,True)]
    last=0
    for it in D["cold_start"]["checkpoints"][1:]:
        lines += [f"ago {it-last}",*cp(rid,it,False)];last=it
    lines += ["stop"]
    return rid,"\n".join(lines)+"\n"

def continuation(s):
    rid=f"XQHP__{s['id']}"
    lines=["% v0.2.4 METRIC-NEUTRAL 200k->400k",
           f"% t={s['t']} role={s['role']}",
           "reset all",f"load __BUNDLE_ROOT__/out/{rid}_i200000.k",*restore(s)]
    # Absolutely no centre/refine/fitto before the first resumed ago.
    last=200000
    for it in D["continuation"]["checkpoints"]:
        lines += [f"ago {it-last}",*cp(rid,it,False)];last=it
    lines += ["stop"]
    return rid,"\n".join(lines)+"\n"

def main():
    for folder in ["kpc_cold_overlap","kpc_cold_extension","kpc_continuation"]:
        (ROOT/folder).mkdir(exist_ok=True)
    for s in D["panel"]:
        rid,txt=cold(s)
        folder="kpc_cold_overlap" if s["role"]=="overlap" else "kpc_cold_extension"
        (ROOT/folder/f"{rid}.kpc").write_text(txt,encoding="utf-8",newline="\n")
        rid,txt=continuation(s)
        (ROOT/"kpc_continuation"/f"{rid}.kpc").write_text(txt,encoding="utf-8",newline="\n")
    print("GENERATE PASS")
    print("  cold overlap   :",len(list((ROOT/'kpc_cold_overlap').glob('*.kpc'))))
    print("  cold extension :",len(list((ROOT/'kpc_cold_extension').glob('*.kpc'))))
    print("  continuation   :",len(list((ROOT/'kpc_continuation').glob('*.kpc'))))
if __name__=="__main__":main()
