#!/usr/bin/env python3
"""A006 v0.4.3b INCREMENTAL patch, for preinstalled v0.4.3 or v0.4.3a.

Only changes the already existing selector dispatch command in run_all.cmd.
Original selection_v043.py and analysis_v043.py remain available and unchanged.
New v0.4.3b files and data use independent names/directories.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, sys
from pathlib import Path

VERSION = 'A006_v0.4.3b_INCREMENTAL'
ADDITIONS = ('tools/selection_v043b.py', 'tools/orientation_v043b.py', 'tools/analysis_v043b.py')
BACKUP = Path('patch_backups') / VERSION
DISPATCH_FROM = b'py -3 "%~dp0tools\\selection_v043.py" %*'
DISPATCH_TO = b'py -3 "%~dp0tools\\selection_v043b.py" %*'
TAG = b'A006_SELECT_DISPATCH_v043'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(root: Path, *, installed_ok=False):
    root = root.resolve()
    required = (
        'run_all.cmd', 'SEED_MANIFEST.json', 'src/build_v040.py',
        'tools/selection_v043.py', 'tools/analysis_v043.py',
        'extensions/borromean/whole/build_whole.py',
    )
    missing = [rel for rel in required if not (root / rel).is_file()]
    if missing:
        raise RuntimeError('Missing required existing v0.4.3 project files: ' + ', '.join(missing))
    manifest = json.loads((root / 'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('version') != '0.4.0' or len(manifest.get('knots', [])) != 13:
        raise RuntimeError('Unexpected A006 seed manifest')
    cmd = (root / 'run_all.cmd').read_bytes()
    if TAG not in cmd:
        raise RuntimeError('Existing v0.4.3 selector dispatcher missing; use cumulative patch on unpatched v0.4.2d')
    if b'A006_SELECT_DISPATCH_v043b' in cmd:
        raise RuntimeError('A v0.4.3b dispatcher already exists; do not patch blindly')
    has_from = len(re.findall(re.escape(DISPATCH_FROM), cmd, flags=re.I))
    has_to = len(re.findall(re.escape(DISPATCH_TO), cmd, flags=re.I))
    receipt = root / BACKUP / 'PATCH_RECEIPT.json'
    if has_to == 1 and receipt.is_file():
        if not installed_ok:
            raise RuntimeError('Incremental v0.4.3b already installed')
        return {'status':'ALREADY_INSTALLED','target':str(root), 'receipt':str(receipt)}
    if has_from != 1 or has_to:
        raise RuntimeError('Unrecognized run_all.cmd selector invocation; no changes made')
    if receipt.exists() or (root / BACKUP).exists():
        raise RuntimeError('Existing incremental backup; refuse overwrite')
    collisions=[str(root/rel) for rel in ADDITIONS if (root/rel).exists()]
    if collisions:
        raise RuntimeError('Patch targets already exist: '+', '.join(collisions))
    payload = Path(__file__).resolve().parent
    if any(not (payload / rel).is_file() for rel in ADDITIONS):
        raise RuntimeError('Incomplete patch payload')
    return {
        'status':'TARGET_PASS', 'target':str(root),
        'existing_selection_module_sha256': sha((root/'tools/selection_v043.py').read_bytes()),
        'existing_selector_has_beadlimit': b'go beadlimit' in (root/'tools/selection_v043.py').read_bytes(),
        'run_all_before_sha256':sha(cmd),
        'new_modules':list(ADDITIONS),
        'existing_data_and_dispatcher_labels_preserved': True,
    }


def apply(root):
    root=Path(root).resolve()
    report=validate(root)
    source=Path(__file__).resolve().parent
    cmdfile=root/'run_all.cmd'
    old=cmdfile.read_bytes()
    new=re.sub(re.escape(DISPATCH_FROM),lambda _: DISPATCH_TO,old,count=1,flags=re.I)
    if old==new or new.count(DISPATCH_TO)!=1:
        raise RuntimeError('Dispatch replacement failed')
    backup=root/BACKUP
    backup.mkdir(parents=True,exist_ok=False)
    (backup/'run_all_before_v043b_incremental.cmd').write_bytes(old)
    written=[]
    try:
        for rel in ADDITIONS:
            dst=root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/rel,dst)
            written.append(dst)
        temp=root/'run_all.v043b_incremental.tmp.cmd'
        temp.write_bytes(new)
        os.replace(temp,cmdfile)
        receipt={**report,'status':'INSTALLED',
                 'run_all_after_sha256':sha(cmdfile.read_bytes()),
                 'installed_module_sha256':{r:sha((root/r).read_bytes()) for r in ADDITIONS},
                 'backup':str(BACKUP),
                 'scientific_status':'STATIC_CANDIDATE; triple-link and Euler unresolved'}
        (backup/'PATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
        return receipt
    except Exception:
        cmdfile.write_bytes(old)
        for p in written:
            p.unlink(missing_ok=True)
        (root/'run_all.v043b_incremental.tmp.cmd').unlink(missing_ok=True)
        raise


def rollback(root):
    root=Path(root).resolve()
    bk=root/BACKUP
    receipt_file=bk/'PATCH_RECEIPT.json'
    if not receipt_file.exists():raise RuntimeError('No incremental receipt; cannot rollback')
    receipt=json.loads(receipt_file.read_text(encoding='utf8'))
    current=(root/'run_all.cmd').read_bytes()
    if sha(current)!=receipt['run_all_after_sha256']:
        raise RuntimeError('run_all.cmd edited since patch; automatic rollback blocked')
    for rel, digest in receipt['installed_module_sha256'].items():
        if sha((root/rel).read_bytes())!=digest:
            raise RuntimeError(f'Module edited since patch: {rel}; rollback blocked')
    origin=bk/'run_all_before_v043b_incremental.cmd'
    if sha(origin.read_bytes())!=receipt['run_all_before_sha256']:
        raise RuntimeError('Backup checksum mismatch; rollback blocked')
    (root/'run_all.cmd').write_bytes(origin.read_bytes())
    for rel in ADDITIONS:(root/rel).unlink()
    # Leave backup and receipt, so that a second install will not overwrite history.
    return {'status':'ROLLED_BACK','original_selection_restored':True,
            'backup_kept_for_audit':str(bk)}


def main():
    p=argparse.ArgumentParser(description='Incremental A006 v0.4.3b patch for preinstalled v0.4.3 or v0.4.3a')
    p.add_argument('--base',type=Path,required=True)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check',action='store_true');mode.add_argument('--apply',action='store_true')
    mode.add_argument('--rollback',action='store_true')
    args=p.parse_args()
    try:
        value=rollback(args.base) if args.rollback else apply(args.base) if args.apply else validate(args.base,installed_ok=True)
        print(json.dumps(value,indent=2));return 0
    except Exception as exc:
        print('PATCH REFUSED:',exc,file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
