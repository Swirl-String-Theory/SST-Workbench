#!/usr/bin/env python3
"""VortexLab A003 P6b guarded patch installer. No overwrites on unknown baselines."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda:file.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(description='Guarded A003 P6b patch; default verify-only')
    ap.add_argument('--root',type=Path,default=Path.cwd(),help='A003_vortexlab project root')
    ap.add_argument('--apply',action='store_true',help='Install with backups after checking exact source hashes')
    args=ap.parse_args()
    package=Path(__file__).resolve().parent
    info=json.loads((package/'manifest.json').read_text(encoding='utf-8'))
    root=args.root.expanduser().resolve()
    if not(root/'apps/web/twist-flow').is_dir():
        sys.exit('REFUSED: project root must contain apps/web/twist-flow (A003_vortexlab).')
    states=[]
    for item in info['files']:
        rel=Path(item['path']);target=root/rel;replacement=package/'payload'/rel
        if not replacement.is_file() or sha(replacement)!=item['patched_sha256']:
            sys.exit('REFUSED: missing/tampered patch payload '+str(rel))
        if not target.is_file():
            sys.exit('REFUSED: required source missing '+str(target))
        current=sha(target)
        label='BASELINE' if current==item['baseline_sha256'] else ('ALREADY_PATCHED' if current==item['patched_sha256'] else 'MODIFIED_OR_UNKNOWN')
        states.append((rel,target,replacement,label,current))
    for rel,_,_,label,current in states:print(f'{label:20s} {rel} SHA256={current}')
    if all(s[3]=='ALREADY_PATCHED' for s in states):
        print('ALREADY INSTALLED: no files modified.');return
    if any(s[3]!='BASELINE' for s in states):
        sys.exit('REFUSED: non-matching sources. All 4 source hashes must match exactly. No files changed.')
    if not args.apply:
        print('VERIFIED: patch compatible. Rerun with --apply to install and create an immutable backup.');return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=root/'.A003_P6b_backups'/stamp
    if backup.exists():sys.exit('REFUSED: backup collision.')
    for rel,target,_,_,_ in states:
        dest=backup/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,dest)
        if sha(dest)!=sha(target):sys.exit('REFUSED: backup verification mismatch; no sources changed.')
    (backup/'manifest.json').write_bytes((package/'manifest.json').read_bytes())
    changed=[]
    try:
        for rel,target,new,_,_ in states:
            fd,tmp=tempfile.mkstemp(prefix='.p6b-',dir=str(target.parent))
            with os.fdopen(fd,'wb') as f:f.write(new.read_bytes());f.flush();os.fsync(f.fileno())
            os.replace(tmp,target)
            changed.append((rel,target))
        for item in info['files']:
            if sha(root/item['path'])!=item['patched_sha256']:raise RuntimeError('postflight hash failed: '+item['path'])
    except Exception:
        for rel,target in changed:shutil.copy2(backup/rel,target)
        raise
    print('PATCH APPLIED AND HASH VERIFIED. Backup:',backup)
    print('NEXT: npm run check; npm start; http://127.0.0.1:4173/twist-flow/')
if __name__=='__main__':main()
