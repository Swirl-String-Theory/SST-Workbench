#!/usr/bin/env python3
"""Transactional additive A006 v0.4.3b install directly onto unpatched v0.4.2d.
Includes generic selector, beadlimit and full-component orientation.
Does not install v0.4.3/v0.4.3a as prerequisites.
"""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil
from pathlib import Path

TAG='A006_SELECT_DISPATCH_v043b'
FILES=('tools/selection_v043b.py','tools/analysis_v043.py','tools/orientation_v043b.py')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check(root):
 root=Path(root).resolve()
 if not (root/'run_all.cmd').is_file() or not (root/'src/build_v040.py').is_file() or not (root/'SEED_MANIFEST.json').is_file():
  raise RuntimeError('Not an A006 v0.4.0 TWIST_TORUS_MATRIX base installation')
 m=json.loads((root/'SEED_MANIFEST.json').read_text(encoding='utf-8'))
 if m.get('version')!='0.4.0' or len(m.get('knots',[]))!=13:
  raise RuntimeError('Unexpected A006 v0.4.0 seed manifest')
 needed=['extensions/borromean/whole/build_whole.py','extensions/borromean/whole/strict_xyz.py',
         'extensions/borromean/whole/metrics_native.py']
 for n in needed:
  if not (root/n).is_file():raise RuntimeError(f'Missing v0.4.2d module: {n}')
 cmds=(root/'run_all.cmd').read_text(encoding='utf-8-sig')
 if not cmds.lower().startswith('@echo off') or ':A006_BORROMEAN_V041' not in cmds:
  raise RuntimeError('Unknown run_all.cmd layout, installation prohibited')
 if TAG in cmds or 'A006_SELECT_DISPATCH_v043' in cmds:
  raise RuntimeError('Selection patch installed already: this cumulative patch targets v0.4.2d only')
 for f in FILES:
  if (root/f).exists():raise RuntimeError('Would overwrite existing file '+f)
 backup=root/'patch_backups'/TAG/'run_all_before_v043b.cmd'
 if backup.exists():raise RuntimeError('Patch backup already exists, installation blocked')
 return {'target':str(root),'source_run_all_sha256':sha(root/'run_all.cmd'),
         'base_seed_manifest_sha256':sha(root/'SEED_MANIFEST.json'),
         'additions':list(FILES),'unchanged':['extensions/borromean/whole','output','Output',
                                           'knotplotrc.kps','existing shortcuts','old campaign datasets'],
         'install_preconditions':'PASS'}

def apply(root):
 report=check(root);root=Path(root).resolve();source=Path(__file__).resolve().parent
 for rel in FILES:
  if not (source/rel).is_file():raise RuntimeError('Missing patch payload '+rel)
 baseline=(root/'run_all.cmd').read_bytes()
 backup=root/'patch_backups'/TAG; backup.mkdir(parents=True,exist_ok=False)
 (backup/'run_all_before_v043b.cmd').write_bytes(baseline)
 original=baseline.decode('utf-8-sig').replace('\r\n','\n')
 dispatch='''rem A006_SELECT_DISPATCH_v043b BEGIN
set "A006_SELECTOR_FIRST=%~1"
if /I "%A006_SELECTOR_FIRST%"=="SELECT" goto A006_SELECT_DISPATCH_v043b
if /I "%A006_SELECTOR_FIRST%"=="RUN" goto A006_SELECT_DISPATCH_v043b
if /I "%A006_SELECTOR_FIRST:~0,2%"=="--" goto A006_SELECT_DISPATCH_v043b
if /I "%A006_SELECTOR_FIRST:~0,5%"=="minN=" goto A006_SELECT_DISPATCH_v043b
if /I "%A006_SELECTOR_FIRST:~0,5%"=="maxN=" goto A006_SELECT_DISPATCH_v043b
rem A006_SELECT_DISPATCH_v043b END
'''
 body=original.split('\n',1)[1]
 combined='@echo off\n'+dispatch+body.rstrip('\r\n')+'''\n:A006_SELECT_DISPATCH_v043b
py -3 "%~dp0tools\\selection_v043b.py" %*
exit /b %errorlevel%
'''
 placed=[]
 try:
  for rel in FILES:
   dest=root/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source/rel,dest);placed.append(dest)
  tmp=root/'run_all.v043b.tmp.cmd'
  tmp.write_text(combined,encoding='utf-8',newline='\r\n')
  os.replace(tmp,root/'run_all.cmd')
  rec={'patch':'A006_v0.4.3b_CUMULATIVE','status':'INSTALLED',
       'v0.4.3_or_v0.4.3a_prerequisite':False,'before':report['source_run_all_sha256'],
       'after':sha(root/'run_all.cmd'),'files':FILES,
       'scientific_gate':'STATIC_CANDIDATE; mu123, knot isotopy and Euler dynamics unresolved'}
  (backup/'PATCH_RECEIPT.json').write_text(json.dumps(rec,indent=2)+'\n')
  return rec
 except Exception:
  (root/'run_all.cmd').write_bytes(baseline)
  for p in placed:p.unlink(missing_ok=True)
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
 g=p.add_mutually_exclusive_group(required=True);g.add_argument('--check',action='store_true');g.add_argument('--apply',action='store_true')
 args=p.parse_args()
 try:print(json.dumps(check(args.base) if args.check else apply(args.base),indent=2))
 except Exception as e:print('PATCH REFUSED:',e);raise SystemExit(2)
