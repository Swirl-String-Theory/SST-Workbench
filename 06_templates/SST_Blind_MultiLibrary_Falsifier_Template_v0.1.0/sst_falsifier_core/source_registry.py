from __future__ import annotations
from pathlib import Path
import os

DEFAULT_CANDIDATES={
"sst_knot_library":["02_libraries/A_knot_libraries/A002_knot_library/A002-v0.2.5","Knot_Library/SST_Knot_Library/SST_Knot_Library_v0.2.5"],
"pklsa":["01_research/E_pipelines/E010_parametric_knot_link_seed_atlas/E010-v0.3.0","01_research/E_pipelines/E010_parametric_knot_link_seed_atlas/E010-v0.1.0","SST_Parametric_Knot_Link_Seed_Atlas_v0.1.0"],
"fremlin":["Ideal_Fremlin_Fseries/fremlin"],
"gilbert":["Ideal_Sources"],
"katlas":["Katlas_Sources_v0.2.2_Outputs"],
"knotplot":["KnotPlot/knots/final"],
}

def workbench_root(): return Path(os.environ.get("SST_WORKBENCH_ROOT",r"C:\workspace\projects\SST-Workbench"))

def resolve_sources(overrides=None):
    root=workbench_root(); overrides=overrides or {}; out={}
    for key,cands in DEFAULT_CANDIDATES.items():
        if key in overrides:
            p=Path(overrides[key]); out[key]={"path":str(p),"exists":p.exists(),"source":"override"}; continue
        found=None
        for rel in cands:
            p=root/rel
            if p.exists(): found=p; break
        out[key]={"path":str(found if found else root/cands[0]),"exists":bool(found),"source":"auto"}
    return out
