from __future__ import annotations
from pathlib import Path
import argparse,hashlib,zipfile


def sha256(path:Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()


def admissible(rel:Path,mode:str):
    parts=set(rel.parts)
    if '_private' in parts or '__pycache__' in parts or '.pytest_cache' in parts:
        return False
    if rel.name.endswith(('.pyc','.pyo')): return False
    if mode=='blind' and rel.name in {'REVEALED_RESULTS.json','REPORT_REVEALED.md'}: return False
    return True


def pack(campaign:Path,mode:str):
    campaign=campaign.resolve()
    if mode=='blind':
        required=['BLIND_MANIFEST.json','BLIND_CONFIG.json','BACKEND_QUALIFICATION.json','BLIND_RESULTS.json','ANALYSIS_BLIND.json','REPORT_BLIND.md','BLIND_SEAL.json']
    else:
        required=['BLIND_SEAL.json','REVEALED_RESULTS.json','REPORT_REVEALED.md']
    missing=[x for x in required if not (campaign/x).is_file()]
    if missing: raise RuntimeError(f'missing required {mode} outputs: {missing}')
    out=Path(str(campaign)+('_BLIND.zip' if mode=='blind' else '_REVEALED.zip'))
    files=sorted(p for p in campaign.rglob('*') if p.is_file() and admissible(p.relative_to(campaign),mode))
    lines=[]
    for p in files:
        rel=p.relative_to(campaign); lines.append(f'{sha256(p)}  {rel.as_posix()}')
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files: z.write(p,Path(campaign.name)/p.relative_to(campaign))
        z.writestr(str(Path(campaign.name)/'ARCHIVE_CONTENTS_SHA256.txt'),'\n'.join(lines)+'\n')
    # Self-audit: private paths must not be present.
    with zipfile.ZipFile(out) as z:
        bad=[n for n in z.namelist() if '/_private/' in n or n.endswith('/_private')]
        if bad: raise RuntimeError(f'private leakage in archive: {bad[:5]}')
    return out


def main():
    p=argparse.ArgumentParser(); p.add_argument('--campaign',required=True); p.add_argument('--mode',choices=['blind','revealed'],required=True)
    a=p.parse_args(); print(pack(Path(a.campaign),a.mode))

if __name__=='__main__': main()
