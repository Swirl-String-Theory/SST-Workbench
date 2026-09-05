from pathlib import Path
import zipfile, json, hashlib
ROOT=Path(__file__).resolve().parent
OUT=ROOT/(ROOT.name+'_outputs.zip')
include=[]
for base in ('analysis','logs','out','runtime_kpc'):
    d=ROOT/base
    if d.exists(): include.extend(p for p in d.rglob('*') if p.is_file())
for name in ('matrix_design.json','README.md','CHANGELOG.md','analysis/EXTENDED_SKIPPED.flag'):
    p=ROOT/name
    if p.is_file(): include.append(p)
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(include)):
        z.write(p,arcname=p.relative_to(ROOT).as_posix())
sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
(OUT.with_suffix(OUT.suffix+'.sha256')).write_text(f'{sha}  {OUT.name}\n',encoding='ascii')
print('OUTPUT PACKAGE:',OUT)
print('SHA256:',sha)
