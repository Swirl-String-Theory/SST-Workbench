#!/usr/bin/env python3
"""A006 v0.5.0c ForceGrid patch; supports v0.5.0a and v0.5.0b root.
Safe add-on: does not edit forcequal v0.5.0b, canonical geometry or old campaigns.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

SRC=Path(__file__).resolve().parent
MARKER='% >>> A006_FORCEGRID_v050c_ALIASES_BEGIN'
END='% <<< A006_FORCEGRID_v050c_ALIASES_END'
BRIDGE='if /I "%~1"=="FORCEGRID" goto forcegrid'
BACKUP=Path('patch_backups/v050c_FORCEGRID')
TARGET=Path('tools/force_grid_v050c.py')

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check(root):
    for name in ('run_all.cmd','knotplotrc.kps','tools/selection_v050.py',
      'Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz'):
      if not (root/name).is_file():raise RuntimeError('Not a compatible v0.5.0a or v0.5.0b root, missing '+name)
    rc=(root/'knotplotrc.kps').read_text(encoding='utf-8-sig')
    cmd=(root/'run_all.cmd').read_text(encoding='utf-8-sig')
    if 'selection_v050.py' not in cmd or not cmd.lstrip().lower().startswith('@echo off') or ':usage' not in cmd:
      raise RuntimeError('Unrecognized run_all.cmd structure')
    if BRIDGE in cmd or MARKER in rc or (root/TARGET).exists() or (root/BACKUP).exists():
      raise RuntimeError('v0.5.0c already installed or partial state: inspect manually')
    for alias in ('fgB0','fgB1','fgB10','fgB100','fgM','fgE','fgA14','fgAM','fgAM0','fgAM2','fgD5','fgD10','fgC10','fgC30'):
      if re.search(r'^\s*alias\s+'+alias+r'\s',rc,re.M|re.I):
        raise RuntimeError('Existing alias collides: '+alias)
    return {'run_all_sha256':hashfile(root/'run_all.cmd'), 'rc_sha256':hashfile(root/'knotplotrc.kps'),
       'baseline':'v0.5.0b' if 'FORCEQUAL' in cmd else 'v0.5.0a'}

def install(root):
    info=check(root)
    sys.path.insert(0,str(SRC/'tools'))
    from force_grid_v050c import ALIASES,read_components,SEED,prepare,selftest
    selftest(root)
    # Abort BEFORE changing dispatcher if planned result folder already exists.
    out=root/'Output/qualification_v050c'
    if out.exists():raise RuntimeError('v0.5.0c output already exists; no overwrite')
    seed=read_components(root/SEED,strict=True)
    if list(map(len,seed))!=[1138,1055,1024]:raise RuntimeError('Unexpected seed bead layout')
    rb=(root/'run_all.cmd').read_text(encoding='utf-8-sig')
    rc=(root/'knotplotrc.kps').read_text(encoding='utf-8-sig')
    newrb=rb.replace('cd /d "%~dp0"','cd /d "%~dp0"\n'+BRIDGE,1)
    block=':forcegrid\npy -3 tools\\force_grid_v050c.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n'
    newrb=newrb.replace(':usage\n',block+':usage\n',1)
    if newrb==rb:raise RuntimeError('Failed to insert dispatcher')
    alias_lines=[MARKER]+[f'alias {short} "read Output/qualification_v050c/scripts/FQ_{arm}.kps"' for arm,short in ALIASES.items()]+[END]
    newrc=rc.rstrip()+'\n\n'+'\n'.join(alias_lines)+'\n'
    # Prepare output in new versioned directory and refuse any existing results.
    shutil.copy2(SRC/TARGET,root/TARGET)
    try:prepare(root)
    except Exception:
      (root/TARGET).unlink(missing_ok=True)
      raise
    back=root/BACKUP;back.mkdir(parents=True,exist_ok=False)
    shutil.copy2(root/'run_all.cmd',back/'run_all.cmd')
    shutil.copy2(root/'knotplotrc.kps',back/'knotplotrc.kps')
    (root/'run_all.cmd').write_text(newrb,encoding='utf-8',newline='\n')
    (root/'knotplotrc.kps').write_text(newrc,encoding='utf-8',newline='\n')
    m={**info,'version':'0.5.0c','status':'INSTALLED',
       'installed_run_all_sha256':hashfile(root/'run_all.cmd'),
       'installed_rc_sha256':hashfile(root/'knotplotrc.kps'),
       'module_sha256':hashfile(root/TARGET),'aliases':ALIASES,
       'note':'v0.5.0a/v0.5.0b legacy runs untouched; experimental KnotPlot runtime not executed'}
    (back/'PATCH_INSTALLED.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    print('INSTALLED: FORCEGRID 14 arms; v0.5.0a/v0.5.0b existing results untouched. Restart KnotPlot.')

def rollback(root):
    back=root/BACKUP
    if not (back/'PATCH_INSTALLED.json').exists():raise RuntimeError('No v0.5.0c backup')
    meta=json.loads((back/'PATCH_INSTALLED.json').read_text())
    for dest,key in [('run_all.cmd','installed_run_all_sha256'),('knotplotrc.kps','installed_rc_sha256'),
      ('tools/force_grid_v050c.py','module_sha256')]:
      if not (root/dest).exists() or hashfile(root/dest)!=meta[key]:
        raise RuntimeError('Current file changed, refusing rollback: '+dest)
    shutil.copy2(back/'run_all.cmd',root/'run_all.cmd')
    shutil.copy2(back/'knotplotrc.kps',root/'knotplotrc.kps')
    print('ROLLBACK: original run_all and rc restored. v0.5.0c output and code retained for audit.')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--base',type=Path,required=True)
    act=ap.add_mutually_exclusive_group(required=True)
    for a in ['check','apply','rollback']:act.add_argument('--'+a,action='store_true')
    a=ap.parse_args();root=a.base.resolve()
    if a.check:print('CHECK PASS:',json.dumps(check(root),indent=2))
    if a.apply:install(root)
    if a.rollback:rollback(root)
if __name__=='__main__':
 try:main()
 except Exception as e:print('PATCH REFUSED:',e,file=sys.stderr);sys.exit(2)
