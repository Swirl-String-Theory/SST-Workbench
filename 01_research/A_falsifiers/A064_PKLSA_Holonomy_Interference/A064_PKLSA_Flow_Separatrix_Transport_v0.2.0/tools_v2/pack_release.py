"""Reproducible source+data ZIP inventory, excluding runtime/build artifacts."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'A064-v0.2.0_SELF_CONTAINED_PROTOTYPE.zip'
EXCLUDE={'.venv','.pytest_cache','__pycache__','build'}

def digest(file):
    h=hashlib.sha256()
    with file.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def files():
    return sorted([f for f in ROOT.rglob('*') if f.is_file()
      and not any(a in EXCLUDE for a in f.relative_to(ROOT).parts)
      and f.suffix not in ('.pyc','.aux','.log','.out')
      and f.name not in ('PACKAGE_MANIFEST.json','MANIFEST_SHA256.txt')])

def main():
    ff=files()
    manifest={'project':'A064','version':'v0.2.0','kind':'MODEL_PROTOTYPE_SELF_CONTAINED',
      'framework_freeze':'NOT_EXECUTED','scientific_status':'UNRESOLVED',
      'files':[{'path':f.relative_to(ROOT).as_posix(),'bytes':f.stat().st_size,'sha256':digest(f)} for f in ff]}
    mf=ROOT/'PACKAGE_MANIFEST.json'
    mf.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (ROOT/'MANIFEST_SHA256.txt').write_text(digest(mf)+'\n')
    with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for f in ff+[mf,ROOT/'MANIFEST_SHA256.txt']:
            z.write(f,ROOT.name+'/'+f.relative_to(ROOT).as_posix())
    (OUT.with_suffix(OUT.suffix+'.sha256')).write_text(digest(OUT)+'  '+OUT.name+'\n')
    with zipfile.ZipFile(OUT) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('Bad zip member '+bad)
    print('ZIP:',OUT,'BYTES:',OUT.stat().st_size,'FILES:',len(manifest['files'])+2)
if __name__=='__main__':main()
