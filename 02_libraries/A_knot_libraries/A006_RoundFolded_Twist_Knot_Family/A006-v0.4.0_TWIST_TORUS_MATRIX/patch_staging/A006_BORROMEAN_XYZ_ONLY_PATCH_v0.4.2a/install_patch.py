#!/usr/bin/env python3
"""Strict v0.4.2 -> 0.4.2a patch. No changes to run_all, shortcuts, knotplotrc, seeds, numerical geometry."""
import argparse, hashlib, json, os, re, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MARKER='XYZ_ONLY_v0.4.2a'

def verify(base):
    if not (base/'SEED_MANIFEST.json').exists():raise ValueError('missing v0.4.0 SEED_MANIFEST.json')
    if json.loads((base/'SEED_MANIFEST.json').read_text()).get('version')!='0.4.0':raise ValueError('wrong base release')
    sub=base/'extensions/borromean/whole'
    if not sub.is_dir():raise ValueError('v0.4.2 whole component patch not installed')
    receipt=json.loads((sub/'PATCH_RECEIPT.json').read_text())
    if receipt.get('patch')!='WHOLE v0.4.2':raise ValueError('Requires unmodified v0.4.2 receipt')
    for name in ('build_whole.py','run_whole.cmd','test_whole.py'):
        if not (sub/name).is_file():raise ValueError('missing '+name)
    if (sub/'strict_xyz.py').exists():raise ValueError('already patched')
    # Fail closed if the original generators were manually modified.
    stock=ROOT/'original_checksums.json'
    wanted=json.loads(stock.read_text())
    for f,w in wanted.items():
        v=hashlib.sha256((sub/f).read_bytes()).hexdigest()
        if v!=w:raise ValueError(f'unrecognized modification in {f}; got {v}; expected {w}')
    out=base/'output/borromean';to_archive=[]
    if out.exists():
        sys.path.insert(0,str(sub))
        import build_whole
        for fp in out.glob('Borromean_5_5_6_*.kpc'):
            name=fp.name
            m=re.fullmatch(r'(Borromean_5_5_6_(?:FLAT|SOFT|BALANCED|TIGHT)_N(?:1024|2048))_(LOAD|TANF_ON_PILOT|TANF_OFF_PILOT)\.kpc',name)
            if not m:continue
            branch='LOAD' if m.group(2)=='LOAD' else ('ON' if 'TANF_ON' in m.group(2) else 'OFF')
            expected=build_whole.kpc_text(m.group(1),branch)
            if fp.read_text()!=expected:raise ValueError('Existing KPC differs from generated original; leave unchanged: '+str(fp))
            to_archive.append(fp)
    backup=base/'patch_backups'/'A006_BORROMEAN_v0.4.2a'
    if backup.exists():raise ValueError('backup directory exists; refuse overwrite')
    return sub,backup,to_archive

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
    x=p.add_mutually_exclusive_group(required=True);x.add_argument('--check',action='store_true');x.add_argument('--apply',action='store_true')
    args=p.parse_args();base=args.base.resolve()
    try:sub,backup,old=verify(base)
    except Exception as exc:sys.exit('PATCH REJECTED: '+str(exc))
    print('TARGET PASS:',base)
    print('Old generated KPC files to archive (not delete):',len(old))
    if args.check:
        print('CHECK PASS; no changes made');return
    try:
        backup.mkdir(parents=True)
        for name in ('build_whole.py','run_whole.cmd'):
            shutil.copy2(sub/name,backup/name)
        for item in old:
            dst=backup/'legacy_kpc'/item.name
            dst.parent.mkdir(exist_ok=True)
            shutil.move(str(item),str(dst))
        for name in ('build_whole.py','run_whole.cmd','strict_xyz.py'):
            shutil.copy2(ROOT/'payload/extensions/borromean/whole'/name,sub/name)
        receipt={'patch':MARKER,'dependency':'WHOLE v0.4.2','archived_load_and_pilot_kpc':len(old),
                 'backup':str(backup.relative_to(base)),'preserved':['run_all.cmd','seeds','old outputs except original generated KPC archived','shortcuts','rc']}
        (sub/'XYZ_ONLY_PATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    except Exception:
        for name in ('build_whole.py','run_whole.cmd'):
            if (backup/name).exists():shutil.copy2(backup/name,sub/name)
        for item in old:
            saved=backup/'legacy_kpc'/item.name
            if saved.exists() and not item.exists():shutil.move(str(saved),str(item))
        (sub/'strict_xyz.py').unlink(missing_ok=True)
        raise
    print('INSTALLED v0.4.2a; no KPC generated, plain xyz-only output')

if __name__=='__main__':main()
