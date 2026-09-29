from pathlib import Path
import json,hashlib,sys,re
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 seal=json.loads((ROOT/'config/SEAL_v0.3.1.json').read_text(encoding='utf-8')); bad=[]
 for rel,h in seal['files'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=h: bad.append(rel)
 if bad: raise SystemExit('SEAL FAIL: '+', '.join(bad))
 cfg=json.loads((ROOT/'config/default.json').read_text(encoding='utf-8'))
 sm=ROOT/cfg['external_geometry_gate']['staged_manifest']
 if sm.exists():
  man=json.loads(sm.read_text(encoding='utf-8'))
  for e in man['entries']:
   p=ROOT/e['file']
   if not p.exists() or sha(p)!=e['sha256']: bad.append(e['carrier_id'])
 if bad: raise SystemExit('STAGED FAIL: '+', '.join(bad))
 print(f'PREFLIGHT PASS: {len(seal["files"])} sealed primary files; staged_manifest={sm.exists()}')
if __name__=='__main__': main()
