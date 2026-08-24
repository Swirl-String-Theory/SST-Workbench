from __future__ import annotations
from pathlib import Path
import json,re,shutil

ROOT=Path(__file__).resolve().parent
D=json.loads((ROOT/"parameter_manifest.json").read_text())

def kpval(v):
    if isinstance(v,str): return v
    if isinstance(v,bool): return "true" if v else "false"
    return f"{v:g}"

def safe_id(v):
    s=kpval(v).replace("-","m").replace(".","p")
    return re.sub(r"[^A-Za-z0-9_]+","_",s)

def baseline_lines():
    # Explicit baseline: never rely on runtime defaults changing.
    return [f"{k} = {kpval(v)}" for k,v in D["baseline"].items()]

def candidate_script(stage,fam,val):
    famname=fam["name"]
    cid=f"{famname}__{safe_id(val)}"
    total=100 if stage=="probe" else 1000
    checkpoint=100 if stage=="probe" else 100
    root_token="__BUNDLE_ROOT__"
    lines=[
        "% AUTO-GENERATED Parameter Effect Atlas v0.3.0",
        f"% FAMILY {famname}",
        f"% VALUE {kpval(val)}",
        "reset all",
        "load 3.1",
        "refine nbeads 300",
        "mode cb",
        "centre",
        "fitto mindist 1.05",
        *baseline_lines(),
    ]
    # Family-specific context overrides baseline before swept assignment.
    for k,v in fam.get("context",{}).items():
        lines.append(f"{k} = {kpval(v)}")
    lines += [
        f"{famname} = {kpval(val)}",
        "centre",
        f"save {root_token}/out/{stage}/{cid}_i00000.k float",
        f"coords {root_token}/out/{stage}/{cid}_i00000.txt",
        f"ago {checkpoint}",
        "centre",
        f"save {root_token}/out/{stage}/{cid}_i00100.k float",
        f"coords {root_token}/out/{stage}/{cid}_i00100.txt",
    ]
    if stage=="extended":
        lines += [
            "ago 900",
            "centre",
            f"save {root_token}/out/{stage}/{cid}_i01000.k float",
            f"coords {root_token}/out/{stage}/{cid}_i01000.txt",
        ]
    lines.append("stop")
    return cid, "\n".join(lines)+"\n"

def main():
    # Bootstrap directories explicitly; empty directories are not guaranteed
    # to survive ZIP packaging/extraction.
    for p in (
        ROOT/"out"/"probe", ROOT/"out"/"extended",
        ROOT/"logs"/"probe", ROOT/"logs"/"extended",
        ROOT/"runtime_kpc"/"probe", ROOT/"runtime_kpc"/"extended",
        ROOT/"analysis", ROOT/"archive",
    ):
        p.mkdir(parents=True, exist_ok=True)

    for stage in ("probe","extended"):
        dd=ROOT/"kpc"/stage
        if dd.exists(): shutil.rmtree(dd)
        dd.mkdir(parents=True)
        index=[]
        for fam in D["families"]:
            for val in fam["values"]:
                cid,text=candidate_script(stage,fam,val)
                p=dd/f"{cid}.kpc"
                p.write_text(text,encoding="utf-8",newline="\n")
                index.append({"candidate":cid,"family":fam["name"],"value":val,"script":str(p.relative_to(ROOT))})
        (dd/"index.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
    print(f"GENERATED {sum(len(f['values']) for f in D['families'])} candidates per stage across {len(D['families'])} parameter families")

if __name__=="__main__":
    main()
