from pathlib import Path
import hashlib,json,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
m=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text())
bad=[]
for r in m['files']:
 p=ROOT/r['path']
 if not p.is_file() or p.stat().st_size!=r['size'] or sha(p)!=r['sha256']: bad.append(r['path'])
print(json.dumps({'files':len(m['files']),'bad':bad,'pass':not bad},indent=2)); raise SystemExit(0 if not bad else 1)
