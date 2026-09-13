from pathlib import Path
import argparse, shutil, re

p=argparse.ArgumentParser(description='Instantiate the reusable SST blind falsifier scaffold.')
p.add_argument('name', help='Long filesystem/output name, e.g. SST_My_Blind_Falsifier')
p.add_argument('package', help='Python experiment package, e.g. sst_my_falsifier')
p.add_argument('destination')
p.add_argument('--version', default='v0.1.0')
p.add_argument('--catalog-id', default='AXXX')
a=p.parse_args()
if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', a.package):
    raise SystemExit('package must be a valid Python identifier')
if not re.fullmatch(r'v\d+\.\d+\.\d+', a.version):
    raise SystemExit('version must look like v0.1.0')

src=Path(__file__).resolve().parents[1]; dst=Path(a.destination)
if dst.exists(): raise SystemExit(f'destination exists: {dst}')
shutil.copytree(src,dst,ignore=shutil.ignore_patterns('.venv','build','__pycache__','.pytest_cache','*.zip','PACKAGE_MANIFEST.json','MANIFEST_SHA256.txt'))
old=dst/'example_experiment'; new=dst/a.package
if old.exists(): old.rename(new)

old_full='SST_Blind_MultiLibrary_Falsifier_Template_v0.1.0'
new_full=f'{a.name}_{a.version}'
repls=[
    (old_full,new_full),
    ('SST_Blind_MultiLibrary_Falsifier_Template',a.name),
    ('example_experiment',a.package),
    ('AXXX',a.catalog_id),
]
for f in dst.rglob('*'):
    if not f.is_file() or f.suffix.lower() not in {'.py','.md','.json','.toml','.cmd','.txt'}: continue
    try: text=f.read_text(encoding='utf-8')
    except Exception: continue
    for old_s,new_s in repls: text=text.replace(old_s,new_s)
    if a.version!='v0.1.0': text=text.replace('v0.1.0',a.version).replace('version="0.1.0"',f'version="{a.version[1:]}"')
    f.write_text(text,encoding='utf-8')
print(f'Created {dst}')
print('Next: define sources/gates/statistic/confirmation/provider/reveal; freeze PREREGISTRATION.md before scientific values are inspected.')
