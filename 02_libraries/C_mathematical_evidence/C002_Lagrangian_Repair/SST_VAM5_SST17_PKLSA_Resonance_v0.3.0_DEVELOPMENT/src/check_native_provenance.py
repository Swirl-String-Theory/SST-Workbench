#!/usr/bin/env python3
"""Optional source provenance checker; NEVER certifies native PKLSA equations."""
import argparse,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--xyz',type=Path,required=True)
p.add_argument('--manifest',type=Path,required=True)
a=p.parse_args()
if not a.xyz.is_file() or not a.manifest.is_file():sys.exit('G5 BLOCKED: missing geometry or signed source manifest')
m=json.loads(a.manifest.read_text(encoding='utf8'))
required=['provider','geometry_sha256','source_commit','source_root','engine_name','core_model','units','reference_clock']
missing=[x for x in required if not m.get(x)]
if missing:sys.exit('G5 BLOCKED: required provenance fields missing: '+', '.join(missing))
real=hashlib.sha256(a.xyz.read_bytes()).hexdigest()
if m['geometry_sha256']!=real:sys.exit('G5 FAIL: geometry digest mismatch')
if m['provider']!='PKLSA' or m['units'] not in ['meters','r_c']:sys.exit('G5 BLOCKED: provider or units invalid')
print('PROVENANCE_PRECHECK_PASS: hashes and metadata only. G5 NATIVE DYNAMICS STILL NOT RUN.')
