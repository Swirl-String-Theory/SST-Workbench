#!/usr/bin/env python3
"""Create-only, fail-closed B007 v0.2.3 HF1 installer. Uses Python standard library."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,sys
from pathlib import Path


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    ap=argparse.ArgumentParser(description='Install bounded float64 analytic parity fix into B007 v0.2.3')
    ap.add_argument('--target',required=True,help='Existing B007 v0.2.3 project root')
    a=ap.parse_args()
    root=Path(__file__).resolve().parent
    target=Path(a.target).resolve()
    man=json.loads((root/'HOTFIX_MANIFEST.json').read_text(encoding='utf-8'))
    if not (target/'run_all.cmd').is_file() or not (target/'src/pipeline.py').is_file():
        raise RuntimeError('Not a B007 project root: '+str(target))
    pr=json.loads((target/'project.json').read_text(encoding='utf-8'))
    if pr.get('version_id')!='v0.2.3':
        raise RuntimeError('Expected unmodified B007 v0.2.3 project, found '+str(pr.get('version_id')))
    backup=target/'.hotfix_backups/HF1'
    if backup.exists():raise RuntimeError('HF1 backup already exists; refusing to overwrite/reapply: '+str(backup))
    # Inspect every path/hash BEFORE creating or replacing anything.
    for rel,expected in man['originals'].items():
        dest=target/rel
        if not dest.is_file() or digest(dest)!=expected:
            raise RuntimeError('Existing file was modified or is the wrong release; REFUSED: '+str(dest))
    for rel,expected in man['patched'].items():
        src=root/'hotfix'/rel
        if not src.is_file() or digest(src)!=expected:
            raise RuntimeError('Hotfix payload invalid: '+str(src))
        dest=target/rel
        if rel not in man['originals'] and dest.exists():
            raise RuntimeError('Would overwrite existing file; REFUSED: '+str(dest))
    # Create additive immutable backups; original release ZIP remains unchanged.
    backup.mkdir(parents=True)
    for rel in man['originals']:
        old=target/rel
        b=backup/rel
        b.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(old,b)
        if digest(b)!=man['originals'][rel]:raise RuntimeError('Backup verification failed: '+str(b))
    # Atomic per-file writes (post-preflight, after verified backups)
    for rel in man['patched']:
        src=root/'hotfix'/rel
        dest=target/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_name(dest.name+'.HF1.tmp')
        if temp.exists():raise RuntimeError('Temporary file already exists: '+str(temp))
        shutil.copyfile(src,temp)
        if digest(temp)!=man['patched'][rel]:raise RuntimeError('Temporary patch corrupted: '+str(temp))
        os.replace(temp,dest)
    (backup/'INSTALL_RECORD.json').write_text(json.dumps({'schema':'B007-HF1-INSTALL-1','target':str(target),
        'previous_hashes':man['originals'],'new_hashes':man['patched'],
        'scientific':'NOT_GRANTED'},indent=2)+'\n',encoding='utf-8')
    print('PASS_HF1_INSTALLED: SHA-256 input and backup verified; patch installed.')
    print('Backups:',backup)
    print('Next: py -m pytest -q tests')
    return 0

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('INSTALL REFUSED / ERROR:',str(exc),file=sys.stderr)
        sys.exit(1)
