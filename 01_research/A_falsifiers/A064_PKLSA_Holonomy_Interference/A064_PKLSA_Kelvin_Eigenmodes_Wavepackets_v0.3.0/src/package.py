"""Immutable package and numerical outputs with a reproducible SHA-256 manifest."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
exclude={'PACKAGE_MANIFEST.json','SHA256SUMS.txt'}
source=[]
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p.name in exclude:continue
    if any(x in ('.venv','__pycache__','.pytest_cache') for x in p.parts):continue
    if p.suffix in ('.aux','.log','.out','.toc','.synctex.gz'):continue
    source.append(p)
manifest={'schema':'SST-A064-v0.3.0-PACKAGE-MANIFEST','files':{str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in source}}
(ROOT/'PACKAGE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(f"{sha(p)}  {p.relative_to(ROOT)}" for p in source)+'\n')
for output,items in [
    (ROOT.parent/(ROOT.name+'.zip'),[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not any(x in ('.venv','__pycache__','.pytest_cache') for x in p.parts) and p.suffix not in ('.aux','.log','.out','.toc')]),
    (ROOT.parent/(ROOT.name+'-outputs.zip'),[p for p in sorted(OUT.rglob('*')) if p.is_file()])]:
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in items:z.write(p,arcname=str(p.relative_to(ROOT.parent)) if p.is_relative_to(ROOT) else p.name)
    with zipfile.ZipFile(output) as z:
        if z.testzip():raise RuntimeError(f'Corrupted ZIP: {output}')
    print(f'{output}: {output.stat().st_size} bytes')
