"""Package checked v0.2.0 source and selected run outputs; never include caches or stale smoke tests."""
from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent
VER=ROOT.name
SOURCE=PARENT/(VER+'_source.zip')
OUTPUTS=PARENT/(VER+'_outputs.zip')
RELEASE=PARENT/(VER+'_RELEASE.zip')
RUNS=('release_pilot_v020','release_highres_v020','release_link_v020')
SRC_FILES=['README.md','requirements.txt','run_all.cmd','run_all.sh','FAMILY.yaml','project.json']

def checksum(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def filter_file(p):
    return p.is_file() and not any(x in p.parts for x in ('__pycache__','.pytest_cache')) and p.suffix!='.pyc'

def write_zip(dest,files):
    if dest.exists():dest.unlink()
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as z:
        for path in files:z.write(path,path.relative_to(PARENT))
    with zipfile.ZipFile(dest) as z:
        corrupted=z.testzip()
        if corrupted:raise RuntimeError('Bad ZIP CRC '+corrupted)
    Path(str(dest)+'.sha256').write_text(checksum(dest)+'  '+dest.name+'\n')
    return (dest.name,dest.stat().st_size,checksum(dest))

def main():
    source=[ROOT/name for name in SRC_FILES]
    source += [p for d in ('src','configs','docs','tests') for p in (ROOT/d).rglob('*') if filter_file(p)]
    assert all(p.is_file() for p in source)
    srcout=ROOT/(VER+'-outputs')/'runs'
    evidence=[]
    for name in RUNS:
        d=srcout/name
        assert (d/'G0_G4_ASSESSMENT.json').is_file()
        ledger=json.loads((d/'G0_G4_ASSESSMENT.json').read_text())
        assert ledger['scientific_status']=='G2_UNRESOLVED_NO_CERTIFIED_EQUILIBRIUM'
        manifest=json.loads((d/'MANIFEST_SHA256.json').read_text())
        for rel,digest in manifest.items():
            p=d/rel
            assert p.is_file() and checksum(p)==digest,(name,rel)
        evidence += [p for p in d.rglob('*') if filter_file(p)]
    if len(set(source+evidence))!=len(source+evidence):raise AssertionError('duplicates')
    result=[]
    result.append(write_zip(SOURCE,sorted(source)))
    result.append(write_zip(OUTPUTS,sorted(evidence)))
    result.append(write_zip(RELEASE,sorted(source+evidence)))
    sha= PARENT/(VER+'_RELEASE_ARCHIVES.sha256')
    sha.write_text('\n'.join(d+'  '+name for name,_,d in result)+'\n')
    print('Verified archive outputs:')
    for name,size,dig in result:print(name,size,dig)
    print('Combined files:',len(source), 'source,',len(evidence),'output')
if __name__=='__main__':main()
