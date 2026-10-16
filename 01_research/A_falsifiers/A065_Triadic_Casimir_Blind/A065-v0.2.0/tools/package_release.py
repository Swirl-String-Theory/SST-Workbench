"""Reproducible ZIP packaging; excludes caches/compiler intermediates."""
from pathlib import Path
import hashlib,json,zipfile,os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent
FSTAMP=(2026,10,14,0,0,0)
EXCLUDE_DIRS={'__pycache__','.pytest_cache','.git','.venv','venv'}
EXCLUDE_SUFFIXES={'.pyc','.pyo','.aux','.log','.out','.toc','.synctex.gz','.fls','.fdb_latexmk','.exe','.dll','.pyd','.o','.obj'}

def included(p):
    rel=p.relative_to(ROOT)
    return not (any(part in EXCLUDE_DIRS for part in rel.parts) or p.suffix in EXCLUDE_SUFFIXES or p.name=='SOURCE_MANIFEST_SHA256.json')

def create_zip(destination,files):
    with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for path,arc in sorted(files,key=lambda x:x[1]):
            info=zipfile.ZipInfo(arc,date_time=FSTAMP)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(0o644<<16)
            z.writestr(info,path.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return hashlib.sha256(destination.read_bytes()).hexdigest()

allfiles=[p for p in ROOT.rglob('*') if p.is_file() and included(p)]
manifest={'schema':'SOURCE_FILES_SHA256_V1','files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(allfiles)},'note':'This file list is not a trusted external signature.'}
manifest_path=ROOT/'SOURCE_MANIFEST_SHA256.json';manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf8')
allfiles=[p for p in ROOT.rglob('*') if p.is_file() and (included(p) or p.name=='SOURCE_MANIFEST_SHA256.json')]
main=OUT/'Triadic_Casimir_Blind_Falsifier_v0.1.0_FULL.zip'
proofs={main.name:create_zip(main,[(p,ROOT.name+'/'+p.relative_to(ROOT).as_posix()) for p in allfiles])}
for ds in ['D01_EULER','D02_CLOCK_LINK','D03_TWO_SURFACE']:
    files=[p for p in (ROOT/'data'/ds).rglob('*') if p.is_file()]
    files.extend([ROOT/'seals'/f'{ds}.seal.json'])
    note=ROOT/'docs'/'BLIND_PROTOCOL.md'
    files.append(note)
    dest=OUT/f'Triadic_Casimir_{ds}_SEALED_v0.1.0.zip'
    proofs[dest.name]=create_zip(dest,[(p,p.relative_to(ROOT).as_posix()) for p in files])
(OUT/'Triadic_Casimir_v0.1.0_ZIP_SHA256SUMS.txt').write_text(''.join(f'{v}  {k}\n' for k,v in proofs.items()),encoding='utf8')
print(json.dumps({'files':proofs,'source_file_count':len(allfiles)},indent=2))
