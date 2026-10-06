from __future__ import annotations
import json
from pathlib import Path

def discover_plan(workbench_root: str|Path):
    root=Path(workbench_root).expanduser().resolve()
    out={'schema':'A053-WORKBENCH-PLAN-v1','workbench_root':str(root),'found':{},'topologies':{k:[] for k in ['3_1','L2a1','L4a1']},'blockers':[]}
    if not root.exists():
        out['blockers'].append('WORKBENCH_ROOT_NOT_FOUND'); return out
    e011=list(root.rglob('E011-v0.2.0'))
    e010=list(root.rglob('E010-v0.3.1'))
    a051=list(root.rglob('A051-v0.1.0'))
    e012=list(root.rglob('E012-v0.1.0'))
    out['found']={'E011':[str(p) for p in e011[:5]],'E010':[str(p) for p in e010[:5]],'A051':[str(p) for p in a051[:5]],'E012':[str(p) for p in e012[:5]]}
    reps=[]
    for p in e011:
        for f in p.rglob('PROVIDER_REPRESENTATIVES.jsonl'):
            try:
                for ln in f.read_text(encoding='utf-8').splitlines():
                    if ln.strip(): reps.append(json.loads(ln))
            except Exception: pass
    for rec in reps:
        blob=json.dumps(rec)
        for topo in out['topologies']:
            if topo in blob: out['topologies'][topo].append(rec)
    for topo,rs in out['topologies'].items():
        if not rs: out['blockers'].append(f'NO_E011_REPRESENTATIVE_{topo}')
    if not e012: out['blockers'].append('E012_DYNAMIC_BRIDGE_NOT_FOUND')
    else: out['blockers'].append('E012_V0_1_0_IS_TREFOIL_FIRST_LINK_MODE_EXTENSION_REQUIRED')
    return out
