from __future__ import annotations
from pathlib import Path
import json
from .blind import run_blind
from .a054_bridge import attach_compound_blind
from .workbench import detect_workbench_root
from .util import load_json,write_json

def run_blind_v3(root:Path,config_path:Path,workbench_root=None,force_python=False,overwrite=False):
    cfg=load_json(config_path)
    out=run_blind(root,config_path,workbench_root,force_python,overwrite)
    if cfg["geometry_mode"]!="workbench_pklsa":
        status={"status":"CI_NO_COMPOUND","reason":"portable CI does not execute Workbench A054 compounds"}
    else:
        wb=detect_workbench_root(workbench_root)
        status=attach_compound_blind(out,wb,cfg["compound_bridge"])
    write_json(out/"BLIND"/"COMPOUND_BRIDGE_STATUS.json",status)
    # A v3 report is additive; the v0.2.1 single-knot report remains as audit evidence.
    gates=json.loads((out/"BLIND"/"GATES.json").read_text(encoding="utf-8"))
    report=f"""# A055 v0.3.0 — integrated BLIND report

## S-branch: isolated knot controls
A055 v0.2.1-style single-knot/counter-channel controls are retained, now with per-(provider,N,m)
mode failure bookkeeping. A missing oscillatory pair in one cell no longer deletes successful
measurements from other mode/resolution cells.

## C-branch: three-component compounds
Status: **{status.get('status')}**

A054 v0.2.x remains the authoritative multi-component dynamics engine. A055 does not rebuild
Triple-Gear or Borromean compounds with a second, divergent implementation.

The blind compound bridge extracts only anonymous dynamical observables:
counter-propagating eigenvalue-pair availability, Kelvin-restricted pair availability,
growth, ringdown, RPO and conditional Floquet status.

No architecture code, 5_2/6_1 slot label, proton/neutron label, mass or charge is available
to the BLIND bridge analysis.

## Interpretation lock
Raw eigenvalue magnitudes from the single-knot and compound branches are not pooled into one
winner score because the projected bases differ. Cross-branch comparison is limited to
pre-registered categorical gates (oscillatory-pair availability, RPO, true-Floquet).
"""
    (out/"BLIND"/"REPORT_BLIND_V3.md").write_text(report,encoding="utf-8")
    write_json(out/"BLIND"/"GATES_V3.json",{
      "single_knot_gates":gates,
      "compound_bridge":status,
      "cross_branch_raw_eigenvalue_pooling":"FORBIDDEN",
      "physical_particle_interpretation":"NOT_OPENED"})
    return out
