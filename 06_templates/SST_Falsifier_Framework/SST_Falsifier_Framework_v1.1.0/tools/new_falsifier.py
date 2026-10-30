from __future__ import annotations
"""Create a fully standalone, immutable SST falsifier instance (v1.1.0)."""
import argparse, hashlib, json, re, secrets, shutil
from pathlib import Path

FRAMEWORK = Path(__file__).resolve().parents[1]
TEMPLATE = FRAMEWORK / 'instance_template'
IGNORE = shutil.ignore_patterns('__pycache__', '.pytest_cache', '*.pyc', '*.pyd', '*.dll', '*.exe',
    '*.lib', '*.exp', '*.obj', 'build', 'dist', '.venv', '.git', '*.egg-info')


def manifest(root: Path) -> dict:
    files = []
    for f in sorted(root.rglob('*')):
        if f.is_file() and f.name != 'RUNTIME_SNAPSHOT_MANIFEST.json':
            files.append({'path': f.relative_to(root).as_posix(), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest(), 'size': f.stat().st_size})
    return {'schema': 'SST-SELF-CONTAINED-RUNTIME-1', 'version': '1.1.0', 'files': files, 'file_count': len(files)}


def generate(catalog_id: str, name: str, destination: str | Path, version='v0.1.0', profile='cpu') -> Path:
    if not re.fullmatch(r'v\d+\.\d+\.\d+', version): raise ValueError('version must look like v0.1.0')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', catalog_id): raise ValueError('invalid catalog ID')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', name): raise ValueError('invalid name')
    dst = Path(destination).resolve()
    if dst.exists(): raise FileExistsError(f'create-only: destination exists: {dst}')
    shutil.copytree(TEMPLATE, dst, ignore=IGNORE)
    # No locally installed framework is ever required, probed, or silently selected.
    internal = dst / '_sst_runtime'
    shutil.copytree(FRAMEWORK, internal, ignore=IGNORE)
    for p in dst.rglob('*'):
        if not p.is_file() or internal in p.parents or p.suffix.lower() not in {'.py','.md','.json','.toml','.cmd','.tex','.txt','.cpp','.hpp','.h'}:
            continue
        t = p.read_text(encoding='utf-8')
        vals={'__CATALOG_ID__':catalog_id, '__NAME__':name, '__VERSION__':version, '__PROFILE__':profile}
        if p.suffix.lower()=='.tex':
            vals={ '@@CATALOG-ID@@':catalog_id, '@@FALSIFIER-NAME@@':name, '@@VERSION@@':version, '@@PROFILE@@':profile }
            esc={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
            vals={k:''.join(esc.get(ch,ch) for ch in v) for k,v in vals.items()}
        for k,v in vals.items(): t=t.replace(k,v)
        p.write_text(t,encoding='utf-8',newline='\n')
    (dst/'.sst_framework_root').unlink(missing_ok=True)
    m=manifest(internal)
    (internal/'RUNTIME_SNAPSHOT_MANIFEST.json').write_text(json.dumps(m,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    (dst/'private').mkdir(exist_ok=True)
    (dst/'private'/'OPAQUE_ID_KEY.bin').write_bytes(secrets.token_bytes(32))
    (dst/'private'/'REVEAL_NONCE.bin').write_bytes(secrets.token_bytes(32))
    print(f'Created standalone {dst}; frozen runtime files: {m["file_count"]}; status: SCIENCE_UNIMPLEMENTED')
    return dst

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('catalog_id');p.add_argument('name');p.add_argument('destination')
    p.add_argument('--profile',choices=['minimal','cpu','gpu','multilibrary_gpu'],default='cpu')
    p.add_argument('--version',default='v0.1.0')
    a=p.parse_args();generate(a.catalog_id,a.name,a.destination,a.version,a.profile)
