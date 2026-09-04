#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

def sha256(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

def main():
 ap=argparse.ArgumentParser(description='Freeze an audit directory before any external comparison.')
 ap.add_argument('audit_dir'); a=ap.parse_args(); root=Path(a.audit_dir)
 if not root.is_dir(): raise SystemExit(f'not a directory: {root}')
 rows=[]
 for p in sorted(x for x in root.rglob('*') if x.is_file() and x.name not in {'FROZEN_MANIFEST.sha256','FROZEN_MANIFEST.json'}):
  rows.append({'path':p.relative_to(root).as_posix(),'sha256':sha256(p),'size_bytes':p.stat().st_size})
 blob=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); digest=hashlib.sha256(blob).hexdigest()
 (root/'FROZEN_MANIFEST.json').write_text(json.dumps({'protocol':'blind-freeze-v1','files':rows,'manifest_sha256':digest},indent=2),encoding='utf-8')
 (root/'FROZEN_MANIFEST.sha256').write_text(digest+'  FROZEN_MANIFEST.json\n',encoding='utf-8')
 print(digest); return 0
if __name__=='__main__': raise SystemExit(main())
