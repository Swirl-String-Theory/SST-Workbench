from __future__ import annotations
from pathlib import Path
import os

def workbench_root(explicit=None):
    if explicit: return Path(explicit)
    return Path(os.environ.get("SST_WORKBENCH_ROOT",r"C:\workspace\projects\SST-Workbench"))

def a054_family(wb):
    p=Path(wb)/"01_research"/"A_falsifiers"/"A054_nucleon_topology_architecture_blind_falsifier"
    if p.is_dir(): return p
    hits=[x for x in (Path(wb)/"01_research").rglob("A054_nucleon_topology_architecture_blind_falsifier") if x.is_dir()]
    if len(hits)!=1: raise FileNotFoundError(f"A054 family missing/ambiguous: {hits}")
    return hits[0]

def a055_v030_output(wb):
    canonical=Path(wb)/"01_research"/"A_falsifiers"/"A055_Blind_Topological_Particle_Spectrum"/"A055-v0.3.0"/"A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.3.0-full-outputs"
    if canonical.is_dir(): return canonical
    hits=[p for p in (Path(wb)/"01_research").rglob("A055_Blind_Topological_Particle_Spectrum_Falsifier_v0.3.0-full-outputs") if p.is_dir()]
    if len(hits)!=1: raise FileNotFoundError(f"A055 v0.3.0 full output missing/ambiguous: {hits}")
    return hits[0]
