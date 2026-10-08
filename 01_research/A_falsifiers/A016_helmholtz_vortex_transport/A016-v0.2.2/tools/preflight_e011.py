from __future__ import annotations
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

try:
    from experiment.e011 import discover_static_ready_carriers
except Exception as ex:
    print(f'[A016:E011 PREFLIGHT] import failure: {type(ex).__name__}: {ex}', flush=True)
    raise SystemExit(5)

mode=(sys.argv[1] if len(sys.argv)>1 else 'FULL').upper()
try:
    carriers,meta=discover_static_ready_carriers(ROOT,mode)
except Exception as ex:
    print('[A016:E011 PREFLIGHT] FAIL', flush=True)
    print(f'  {type(ex).__name__}: {ex}', flush=True)
    print('  Expected canonical dependency:', flush=True)
    print(r'  SST-Workbench\01_research\E_pipelines\E011_sklsa_selected_knot_link_seed_atlas\E011-v0.3.0', flush=True)
    print('  Required E011 output: E011_SKLSA_Static_Ready_Seed_Atlas_v0.3.0-outputs', flush=True)
    raise SystemExit(5)
print('[A016:E011 PREFLIGHT] PASS', flush=True)
print(f"  mode population : {meta.get('selected_manifest')}", flush=True)
print(f"  admitted        : {meta.get('n_admitted_carriers')} carriers", flush=True)
print(f"  topologies      : {meta.get('n_distinct_topologies')}", flush=True)
print(f"  multi-provider  : {meta.get('n_multi_provider_topologies')}", flush=True)
print(f"  E011            : {meta.get('e011_version')} / {meta.get('e011_execution_gate')}", flush=True)
print(f"  E010 parent     : {meta.get('e010_release_version')}", flush=True)
print(f"  bundle          : {meta.get('bundle_path')}", flush=True)
raise SystemExit(0)
