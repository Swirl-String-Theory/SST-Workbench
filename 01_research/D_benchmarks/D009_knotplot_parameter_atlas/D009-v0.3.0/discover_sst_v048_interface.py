from __future__ import annotations
from pathlib import Path
import json, os, re, sys

ROOT=Path(__file__).resolve().parent
TARGET="SST_MultiTopology_Knot_Link_TBK_RPO_Falsifier_v0.4.8_Adaptive_Spectral_DD32_compact"

def workspace_root():
    # Expected: ...\SST-Workbench\KnotPlot\<atlas>
    if ROOT.parent.name.lower()=="knotplot":
        return ROOT.parent.parent
    return ROOT.parent

def scan_text(path):
    try:
        t=path.read_text(encoding="utf-8",errors="replace")
    except Exception:
        return {}
    keys={}
    for term in ("argparse","dataset","input","geometry","xyz","config","run_all","run_extended","rpo","tbk","spectral","dd32"):
        hits=[line.strip() for line in t.splitlines() if term.lower() in line.lower()]
        if hits: keys[term]=hits[:8]
    return keys

def main():
    wr=workspace_root()
    env=os.environ.get("SST_V048_DIR","").strip()
    candidates=[]
    if env:
        p=Path(env)
        if p.is_dir(): candidates=[p]
    if not candidates and wr.is_dir():
        try:
            candidates=[p for p in wr.rglob(TARGET) if p.is_dir()]
        except Exception:
            candidates=[]
    out={"target":TARGET,"workspace_root":str(wr),"found":[str(p) for p in candidates]}
    if candidates:
        p=candidates[0]
        cmds=sorted([q for q in p.glob("*.cmd") if q.is_file()])
        pys=sorted([q for q in p.glob("*.py") if q.is_file()])
        docs=sorted([q for q in list(p.glob("README*"))+list(p.glob("CHANGELOG*")) if q.is_file()])
        out["selected"]=str(p)
        out["root_cmds"]=[q.name for q in cmds]
        out["root_python"]=[q.name for q in pys]
        out["docs"]=[q.name for q in docs]
        out["static_interface_hints"]={}
        for q in (cmds+pys+docs)[:30]:
            hints=scan_text(q)
            if hints: out["static_interface_hints"][q.name]=hints
        out["status"]="FOUND_INTERFACE_NOT_INVOKED"
        out["reason"]="The bridge does not guess command-line arguments. Use this discovery report or provide the package archive so the adapter can be wired against its actual interface."
    else:
        out["status"]="NOT_FOUND"
        out["reason"]="Exact v0.4.8 compact directory was not found under the SST-Workbench workspace. Set SST_V048_DIR or place the package in the workspace."
    ad=ROOT/"analysis"; ad.mkdir(parents=True,exist_ok=True)
    (ad/"SST_V048_DISCOVERY.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
    md=["# SST v0.4.8 Adaptive Spectral DD32 compact — interface discovery","",
        f"- Status: **{out['status']}**",
        f"- Workspace: `{out['workspace_root']}`",
        f"- Target: `{TARGET}`",""]
    if candidates:
        md += [f"- Selected: `{out['selected']}`","",
               "## Root CMD entry points"] + [f"- `{x}`" for x in out.get("root_cmds",[])]
        md += ["","## Root Python entry points"] + [f"- `{x}`" for x in out.get("root_python",[])]
        md += ["","## Static interface hints","```json",json.dumps(out.get("static_interface_hints",{}),indent=2),"```"]
    md += ["","## Safety policy",out["reason"]]
    (ad/"SST_V048_DISCOVERY.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    print("\n".join(md))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
