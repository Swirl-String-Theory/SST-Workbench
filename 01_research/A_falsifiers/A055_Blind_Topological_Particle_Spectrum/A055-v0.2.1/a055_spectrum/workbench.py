from __future__ import annotations
import os
from pathlib import Path

def detect_workbench_root(explicit=None) -> Path:
    if explicit:
        p=Path(explicit).expanduser().resolve()
        if (p/"01_research").is_dir():
            return p
        raise FileNotFoundError(f"Not an SST-Workbench root: {p}")
    env=os.environ.get("SST_WORKBENCH_ROOT")
    if env:
        return detect_workbench_root(env)
    here=Path(__file__).resolve()
    for p in [here.parent,*here.parents]:
        if (p/"01_research").is_dir():
            return p
    canonical=Path(r"C:\workspace\projects\SST-Workbench")
    if canonical.exists():
        return canonical.resolve()
    raise FileNotFoundError("SST-Workbench root not found; pass --workbench-root")

def _unique(paths, what):
    xs=[]; seen=set()
    for p in paths:
        p=Path(p)
        if p.exists():
            q=p.resolve()
            if q not in seen:
                xs.append(q); seen.add(q)
    if len(xs)==1: return xs[0]
    if not xs: raise FileNotFoundError(f"{what} not found")
    raise RuntimeError(f"Ambiguous {what}: " + "; ".join(map(str,xs)))

def find_e011_version(workbench: Path) -> Path:
    exact=workbench/"01_research"/"E_pipelines"/"E011_sklsa_selected_knot_link_seed_atlas"/"E011-v0.3.0"
    candidates=[exact]
    candidates += list((workbench/"01_research").rglob("E011_sklsa_selected_knot_link_seed_atlas/E011-v0.3.0"))
    return _unique(candidates,"E011-v0.3.0")

def find_e011_seedset(workbench: Path, topology_id: str) -> Path:
    v=find_e011_version(workbench)
    candidates=list(v.glob(f"*-outputs/topologies/{topology_id}/STATIC_READY_SEEDSET.json"))
    candidates += list(v.rglob(f"topologies/{topology_id}/STATIC_READY_SEEDSET.json"))
    return _unique(candidates,f"E011 {topology_id} STATIC_READY_SEEDSET.json")

def find_c006_version(workbench: Path) -> Path:
    candidates=list((workbench/"01_research").rglob("C006_kelvin_floquet_workbench/C006-v0.3.0"))
    return _unique(candidates,"C006-v0.3.0")

def rewrite_workbench_path(source_path: str, workbench: Path) -> Path:
    raw=str(source_path)
    p=Path(raw)
    if p.exists(): return p.resolve()
    norm=raw.replace("/","\\")
    marker="SST-Workbench\\"
    idx=norm.lower().find(marker.lower())
    if idx>=0:
        suffix=norm[idx+len(marker):].replace("\\",os.sep)
        return (workbench/suffix).resolve()
    return (workbench/raw.replace("\\",os.sep).replace("/",os.sep)).resolve()
