#!/usr/bin/env python3
"""Fail-closed A006 v0.4.2d in-place installer, user-provided v0.4.2c hash-bound.

Never alters run_all, RC, shortcuts, XYZ, preexisting campaigns.
"""
import argparse, hashlib, json, os, shutil, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
MAN=json.loads((HERE/'PATCH_MANIFEST.json').read_text())
RECEIPT=Path('extensions/borromean/whole/METRICS_PATCH_RECEIPT_v042d.json')

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(base):
    base=Path(base).resolve()
    if base.name!='A006-v0.4.0_TWIST_TORUS_MATRIX':
        raise RuntimeError(f'Wrong target directory: {base}')
    for f in ('run_all.cmd','SEED_MANIFEST.json','extensions/borromean/whole/SCALE_PATCH_RECEIPT.json'):
        if not (base/f).is_file():raise RuntimeError(f'Missing prerequisite: {f}')
    if json.loads((base/'SEED_MANIFEST.json').read_text()).get('version')!='0.4.0':
        raise RuntimeError('Native v0.4.0 seed manifest required')
    if (base/RECEIPT).exists():raise RuntimeError('Already installed; not overwriting')
    for rel,sha in MAN['source_hashes'].items():
        f=base/rel
        if not f.is_file() or digest(f)!=sha:raise RuntimeError(f'Base file hash mismatch: {rel}')
    for rel in MAN['files']:
        src=HERE/'payload'/rel;dst=base/rel
        if not src.is_file():raise RuntimeError(f'Patch payload missing: {rel}')
        if dst.exists() and rel not in MAN['source_hashes']:
            raise RuntimeError(f'New file conflicts with existing base file: {rel}')
    return base

def apply(base):
    base=validate(base)
    backup=base/'patch_backups'/'A006_BORROMEAN_v0.4.2d'
    if backup.exists():raise RuntimeError('Backup destination already exists; refuse install')
    orig=[];new=[]
    try:
        for rel in MAN['source_hashes']:
            dst=backup/rel;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(base/rel,dst);orig.append(rel)
        for rel in MAN['files']:
            src=HERE/'payload'/rel;dst=base/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            temp=dst.with_name(dst.name+'.installtmp')
            if temp.exists():raise FileExistsError(temp)
            shutil.copy2(src,temp);os.replace(temp,dst)
            if rel not in MAN['source_hashes']:new.append(rel)
        receipt={'patch':'v0.4.2d','source_base':'A006-v0.4.0 + v0.4.2c',
                 'modified':list(MAN['source_hashes']),'added':new,
                 'backup':str(backup.relative_to(base)),
                 'run_all_untouched':True,'xyz_untouched':True,
                 'KnotPlot_runtime':'NOT_TESTED','Milnor_mu123':'UNRESOLVED'}
        (base/RECEIPT).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    except Exception:
        for rel in orig:
            saved=backup/rel
            if saved.is_file():shutil.copy2(saved,base/rel)
        for rel in new:(base/rel).unlink(missing_ok=True)
        raise
    print('INSTALLED v0.4.2d — run_all.cmd, all XYZ, RC and shortcuts untouched')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base',required=True,type=Path)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--check',action='store_true');group.add_argument('--apply',action='store_true')
    args=ap.parse_args()
    try:
        if args.check:
            b=validate(args.base);print('CHECK PASS:',b,' — no changes made')
        else:apply(args.base)
    except Exception as e:
        print('REFUSED:',e,file=sys.stderr);raise SystemExit(1)
