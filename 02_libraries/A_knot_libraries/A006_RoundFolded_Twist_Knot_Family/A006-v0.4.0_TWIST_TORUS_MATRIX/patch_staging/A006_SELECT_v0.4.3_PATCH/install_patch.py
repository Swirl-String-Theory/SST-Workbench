#!/usr/bin/env python3
"""Install additive v0.4.3 A006 selector. No modification to existing experiment files."""
import argparse,hashlib,json,os,re,shutil,tempfile
from pathlib import Path

FILES=('tools/selection_v043.py','tools/analysis_v043.py')
TAG='A006_SELECT_DISPATCH_v043'

def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def check(root):
 root=Path(root).resolve()
 if not (root/'run_all.cmd').is_file() or not (root/'src'/'build_v040.py').is_file() or not (root/'SEED_MANIFEST.json').is_file():
  raise RuntimeError('Not the A006 v0.4.0 TWIST_TORUS_MATRIX root')
 mani=json.loads((root/'SEED_MANIFEST.json').read_text(encoding='utf8'))
 if mani.get('version')!='0.4.0' or len(mani.get('knots',[]))!=13:
  raise RuntimeError('Unexpected A006 manifest; refuse unverified target')
 if not (root/'extensions'/'borromean'/'whole'/'build_whole.py').is_file():
  raise RuntimeError('Whole-component Borromean patch missing')
 src=(root/'run_all.cmd').read_bytes()
 if TAG.encode() in src:raise RuntimeError('v0.4.3 already installed; refuse duplicate')
 if b'A006_BORROMEAN_V041' not in src:raise RuntimeError('Unknown run_all.cmd dispatcher layout')
 for f in FILES:
  if (root/f).exists():raise RuntimeError('Would overwrite existing file '+f)
 return {'root':str(root),'run_all_sha256':hashfile(root/'run_all.cmd'),
         'manifest_knots':len(mani['knots']),'new_files':list(FILES),'old_geometry_unchanged':True}

def apply(root):
 report=check(root);root=Path(root).resolve();source=Path(__file__).resolve().parent
 origin=root/'run_all.cmd';s=origin.read_text(encoding='utf-8-sig').replace('\r\n','\n')
 if not s.lower().startswith('@echo off'):raise RuntimeError('Unexpected run_all.cmd header')
 # Detect optional RUN / SELECT or first key-value argument, keeping all legacy commands unchanged.
 dispatch='''rem A006_SELECT_DISPATCH_v043 BEGIN -- additive generic selector
set "A006_SELECTOR_FIRST=%~1"
if /I "%A006_SELECTOR_FIRST%"=="SELECT" goto A006_SELECT_DISPATCH_v043
if /I "%A006_SELECTOR_FIRST%"=="RUN" goto A006_SELECT_DISPATCH_v043
if /I "%A006_SELECTOR_FIRST:~0,2%"=="--" goto A006_SELECT_DISPATCH_v043
if /I "%A006_SELECTOR_FIRST:~0,5%"=="minN=" goto A006_SELECT_DISPATCH_v043
if /I "%A006_SELECTOR_FIRST:~0,5%"=="maxN=" goto A006_SELECT_DISPATCH_v043
rem A006_SELECT_DISPATCH_v043 END
'''
 body=s.split('\n',1)[1]
 combined='@echo off\n'+dispatch+body.rstrip('\r\n')+'''\n:A006_SELECT_DISPATCH_v043
py -3 "%~dp0tools\\selection_v043.py" %*
exit /b %errorlevel%
'''
 backup=root/'patch_backups'/'selection_v043';backup.mkdir(parents=True,exist_ok=True)
 before=backup/'run_all_before_v043.cmd'
 if before.exists():raise RuntimeError('Existing backup blocks installation; inspect manually')
 # Stage changes first. Back up original before replacing.
 before.write_bytes(origin.read_bytes())
 installed=[]
 try:
  for f in FILES:
   dest=root/f;dest.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(source/f,dest);installed.append(dest)
  tmp=origin.with_name('run_all.v043.tmp.cmd')
  tmp.write_text(combined,encoding='utf-8',newline='\r\n')
  os.replace(tmp,origin)
  receipt={'status':'INSTALLED','base_run_all_sha256':report['run_all_sha256'],
           'new_run_all_sha256':hashfile(origin),'files':[str(p.relative_to(root)) for p in installed],
           'original_run_all_backup':str(before.relative_to(root)),
           'scientific_status':'STATIC_CANDIDATE; KnotPlot runtime and topology not certified'}
  (backup/'PATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
  return receipt
 except Exception:
  origin.write_bytes(before.read_bytes())
  for p in installed:p.unlink(missing_ok=True)
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True)
 mode=p.add_mutually_exclusive_group(required=True);mode.add_argument('--check',action='store_true');mode.add_argument('--apply',action='store_true')
 a=p.parse_args()
 try:
  print(json.dumps(check(a.base) if a.check else apply(a.base),indent=2))
 except Exception as e:
  print('INSTALL BLOCKED:',e);raise SystemExit(2)
