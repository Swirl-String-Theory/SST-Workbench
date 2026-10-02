from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"balance_design.json").read_text())

def val(x):
    if isinstance(x,str):return x
    if isinstance(x,bool):return "true" if x else "false"
    return f"{x:.15g}"

def restore(s):
    out=["mode cb","collision fast","energy model MD"]
    for k,v in D["frozen_non_qhp_baseline"].items():out.append(f"{k} = {val(v)}")
    out += [f"charge = {val(s['charge'])}",f"hooke = {val(s['hooke'])}",f"power = {val(s['power'])}"]
    return out

def probe(s):
    rid=f"K31__{s['id']}"
    return rid,"\n".join([
        "% v0.2.3 metric-neutral 100k reload probe",
        "reset all",f"load __BUNDLE_ROOT__/out/{rid}_i100000.k",*restore(s),
        f"coords __BUNDLE_ROOT__/analysis/resume_checks/{rid}_i100000_reload.txt",
        "stop",""
    ])

def checkpoint(rid,it):
    tag=f"i{it:05d}";o="__BUNDLE_ROOT__/out"
    return ["centre","safe","dowker","lnknum","length","distance","angle","acn",
            f"save {o}/{rid}_{tag}.k float",f"coords {o}/{rid}_{tag}.txt"]

def continuation(s):
    rid=f"K31__{s['id']}"
    lines=["% v0.2.3 metric-neutral 100k->200k",
           "reset all",f"load __BUNDLE_ROOT__/out/{rid}_i100000.k",*restore(s)]
    last=100000
    for it in D["continuation"]["additional_checkpoints"]:
        lines += [f"ago {it-last}",*checkpoint(rid,it)]
        last=it
    lines += ["stop",""]
    return rid,"\n".join(lines)

def main():
    for folder in ["kpc_probe","kpc_continuation"]:(ROOT/folder).mkdir(exist_ok=True)
    for s in D["settings"]:
        rid,t=probe(s);(ROOT/"kpc_probe"/f"{rid}.kpc").write_text(t,encoding="utf-8",newline="\n")
        rid,t=continuation(s);(ROOT/"kpc_continuation"/f"{rid}.kpc").write_text(t,encoding="utf-8",newline="\n")
    print("GENERATE PASS: 20 probes + 20 100k->200k continuations")
if __name__=="__main__":main()
