from pathlib import Path
import json,os,shutil,subprocess,sys,tempfile,hashlib
import numpy as np

HERE=Path(__file__).resolve()
PKG=HERE.parents[1]
D=json.loads((PKG/"reference/Trefoil_Balance_Point_Campaign_v0.1.0_balance_design.json").read_text())
assert D["n_settings"]==10 and D["n_variants"]==2

# Structural blinding policy.
src=(PKG/"bridge.py").read_text()
assert '"source":r["source"]' in src
assert '"charge":r["charge"]' not in src[src.find("def mode_entries"):src.find("def call_run_panel")]
assert '"canonical_id":"3_1"' in src

print("STATIC HANDOFF SELFTEST PASS")
