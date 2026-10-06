from pathlib import Path
import argparse,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--config',default='config/default.json'); a=ap.parse_args()
 seal=json.loads((ROOT/'config/SEAL_v0.3.2.json').read_text(encoding='utf-8')); bad=[]
 for rel,h in seal['files'].items():
  p=ROOT/rel
  if not p.exists() or sha(p)!=h: bad.append(rel)
 if bad: raise SystemExit('SEAL FAIL: '+', '.join(bad))
 cfg=json.loads((ROOT/a.config).read_text(encoding='utf-8'))
 sm=ROOT/cfg['external_geometry_gate']['staged_manifest']
 if sm.exists():
  man=json.loads(sm.read_text(encoding='utf-8'))
  for e in man['entries']:
   p=ROOT/e['file']
   if not p.exists() or sha(p)!=e['sha256']: bad.append(e['carrier_id'])
 if bad: raise SystemExit('STAGED FAIL: '+', '.join(bad))
 parent=ROOT/cfg['branch_phase_gate']['parent_evidence']
 if not parent.exists(): raise SystemExit('PARENT EVIDENCE FAIL: missing '+str(parent.relative_to(ROOT)))
 print(f'PREFLIGHT PASS: {len(seal["files"])} sealed primary files; config={a.config}; staged_manifest={sm.exists()}')
if __name__=='__main__': main()
