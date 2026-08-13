#!/usr/bin/env python3
from __future__ import annotations
import json
from sst_pf_binary_falsifier.core import linear_euler_bulk_wave_gate, write_json

def main() -> int:
    r=linear_euler_bulk_wave_gate(); write_json('audit_out/linear_euler_gate.json',r); print(json.dumps(r,indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
