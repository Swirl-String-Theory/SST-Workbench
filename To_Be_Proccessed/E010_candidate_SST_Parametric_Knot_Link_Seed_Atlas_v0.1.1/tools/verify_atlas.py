from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def runtime_bytecode(rel):
 p=Path(rel)
 return "__pycache__" in p.parts or p.suffix.lower()==".pyc"
m=json.loads((ROOT/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
bad=[]
portable=[]
ignored_runtime=[]
for r in m['files']:
 if runtime_bytecode(r['path']):
  ignored_runtime.append(r['path'])
  continue
 portable.append(r)
 p=ROOT/r['path']
 if not p.is_file() or p.stat().st_size!=r['size'] or sha(p)!=r['sha256']:
  bad.append(r['path'])
print(json.dumps({
 'format':'SST-PKLSA-VERIFY-0.1.1',
 'manifest_records':len(m['files']),
 'portable_records_checked':len(portable),
 'ignored_runtime_bytecode':ignored_runtime,
 'bad':bad,
 'pass':not bad
},indent=2))
raise SystemExit(0 if not bad else 1)
