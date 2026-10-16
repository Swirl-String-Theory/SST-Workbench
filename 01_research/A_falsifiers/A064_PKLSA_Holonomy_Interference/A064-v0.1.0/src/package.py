from pathlib import Path
import hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT.parent
SKIP={'.venv','.pytest_cache','__pycache__','.git'}
def included():
    for p in sorted(ROOT.rglob('*')):
        if not p.is_file() or any(q in SKIP for q in p.relative_to(ROOT).parts) or p.suffix in {'.pyc','.aux','.log','.out','.toc'}:
            continue
        if p.name in {'SHA256SUMS.txt'}:continue
        yield p

def main():
    paths=list(included())
    digest=['%s  %s'%(hashlib.sha256(p.read_bytes()).hexdigest(),p.relative_to(ROOT).as_posix()) for p in paths]
    manifest=ROOT/'SHA256SUMS.txt'
    manifest.write_text('\n'.join(digest)+'\n',encoding='utf-8')
    full=PARENT/(ROOT.name+'.zip')
    with zipfile.ZipFile(full,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for p in paths+[manifest]:z.write(p,arcname=(ROOT.name+'/'+p.relative_to(ROOT).as_posix()))
    output=PARENT/(ROOT.name+'-outputs.zip')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=8) as z:
        for p in sorted((ROOT/'outputs').iterdir()):
            if p.is_file():z.write(p,arcname=p.name)
    print(full);print(output)
if __name__=='__main__':main()
