from pathlib import Path
import zipfile,hashlib,json
R=Path(__file__).resolve().parents[1];O=R/(R.name+'-outputs')
archive=R.parent/(R.name+'_outputs.zip')
# Always rebuild manifests LAST, so extended reruns cannot invalidate top-level hashes.
root_results=[O] + ([O/'extended'] if (O/'extended').is_dir() else [])
if not any((d/'G0_G4_ASSESSMENT.json').exists() and (d/'FALSIFIER_REPORT.pdf').exists() for d in root_results):
 raise FileNotFoundError('No completed PDF/report output root')
for d in reversed(root_results):
 if not (d/'G0_G4_ASSESSMENT.json').exists() or not (d/'FALSIFIER_REPORT.pdf').exists():continue
 manifest={p.relative_to(d).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(d.rglob('*')) if p.is_file() and p.name!='MANIFEST_SHA256.json'}
 (d/'MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')

with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(R.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and not p.name.endswith('.pyc'):
   z.write(p,p.relative_to(R.parent))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 digest=hashlib.sha256(archive.read_bytes()).hexdigest()
sha=Path(str(archive)+'.sha256');sha.write_text(f'{digest}  {archive.name}\n')
print('ARCHIVE',archive,'SHA256',digest,'BYTES',archive.stat().st_size)
