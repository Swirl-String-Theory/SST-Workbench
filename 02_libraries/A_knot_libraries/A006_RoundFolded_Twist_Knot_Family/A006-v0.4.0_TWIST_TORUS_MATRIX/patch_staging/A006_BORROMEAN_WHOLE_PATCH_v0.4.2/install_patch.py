#!/usr/bin/env python3
"""Fail-closed add-on to the installed A006 0.4.0 + Borromean 0.4.1 extension.

Patches only extensions/borromean/run_borromean.cmd and adds whole/ subtree.
Does not touch run_all.cmd, existing .kpt seeds, shortcuts, RC or previous output.
"""
import argparse,hashlib,json,os,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MARK='A006_BORROMEAN_WHOLE_V042'

def sha(x):return hashlib.sha256(Path(x).read_bytes()).hexdigest()

def verify(root):
    req=['run_all.cmd','SEED_MANIFEST.json','extensions/borromean/build_borromean.py',
         'extensions/borromean/run_borromean.cmd','extensions/borromean/PATCH_RECEIPT.json']
    for s in req:
        if not (root/s).is_file():raise RuntimeError('Missing dependency '+s)
    meta=json.loads((root/'SEED_MANIFEST.json').read_text())
    if meta.get('version')!='0.4.0' or meta.get('count')!=26:
        raise RuntimeError('Not A006 v0.4.0 TWIST_TORUS_MATRIX')
    receipt=json.loads((root/'extensions/borromean/PATCH_RECEIPT.json').read_text())
    if receipt.get('patch')!='BORROMEAN v0.4.1':raise RuntimeError('Requires installed v0.4.1')
    r=root/'extensions/borromean/run_borromean.cmd';b=r.read_bytes()
    s=b.decode('utf-8-sig')
    if 'if /I "%~1"=="TEST"' not in s or 'if /I "%~1"=="BUILD"' not in s:
        raise RuntimeError('Unknown run_borromean.cmd structure')
    if MARK in s or (root/'extensions/borromean/whole').exists():
        raise RuntimeError('Already patched, refuse to overwrite')
    if (root/'patch_backups'/'A006_BORROMEAN_v0.4.2'/'run_borromean.cmd.before').exists():
        raise RuntimeError('Existing backup conflict')
    # Never modify pre-existing v0.4.0 output, including old v0.4.1 decorated links.
    assert (root/'extensions/borromean/build_borromean.py').exists()
    return r,b,s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True)
    m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--check',action='store_true');m.add_argument('--apply',action='store_true')
    x=ap.parse_args();root=x.base.resolve()
    try:r,b,s=verify(root)
    except Exception as e:sys.exit('PATCH NOT APPLIED: '+str(e))
    print('TARGET PASS',root,'\nWRAPPER SHA256',hashlib.sha256(b).hexdigest())
    if x.check:
        print('CHECK ONLY PASS — no files changed.')
        return
    dest=root/'extensions/borromean/whole'
    backup=root/'patch_backups'/'A006_BORROMEAN_v0.4.2'/'run_borromean.cmd.before'
    tmp=r.with_suffix('.cmd.v042.tmp')
    newline='\r\n' if b'\r\n' in b else '\n'
    hook=f'if /I "%~1"=="WHOLE" (\n call "%~dp0whole\\run_whole.cmd" %2 %3 %4 %5 %6 %7 %8 %9\n exit /b %errorlevel%\n)\n'
    # Insert after @echo off (before setlocal), preserving existing wrapper contents.
    lines=s.splitlines(keepends=True)
    if not lines or lines[0].strip().lower()!='@echo off':sys.exit('PATCH NOT APPLIED: invalid wrapper header')
    new=lines[0]+f'rem {MARK}'+newline+hook.replace('\n',newline)+''.join(lines[1:])
    try:
        backup.parent.mkdir(parents=True,exist_ok=True)
        backup.write_bytes(b)
        shutil.copytree(ROOT/'payload/extensions/borromean/whole',dest)
        tmp.write_bytes(new.encode('utf-8'))
        os.replace(tmp,r)
        (dest/'PATCH_RECEIPT.json').write_text(json.dumps({
            'target':'A006 v0.4.0 with 0.4.1', 'patch':'WHOLE v0.4.2',
            'wrapper_sha_before':sha(backup),'wrapper_sha_after':sha(r),
            'changed':['extensions/borromean/run_borromean.cmd','extensions/borromean/whole'],
            'preserved':['run_all.cmd','output/seeds','knotplotrc','shortcut','prior campaigns','legacy decorated outputs'],
            'KnotPlot_runtime':'NOT_RUN'},indent=2)+'\n')
    except Exception:
        if backup.exists():r.write_bytes(b)
        if dest.exists():shutil.rmtree(dest)
        if tmp.exists():tmp.unlink()
        raise
    print('PATCH INSTALLED. run_all.cmd BORROMEAN WHOLE TEST / BUILD / PILOT')

if __name__=='__main__':main()
