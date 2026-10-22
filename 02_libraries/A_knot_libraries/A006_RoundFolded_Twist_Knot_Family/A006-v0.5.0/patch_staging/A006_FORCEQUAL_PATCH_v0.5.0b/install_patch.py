#!/usr/bin/env python3
"""Install independent FORCEQUAL command + alias set into A006 v0.5.0a only.

Never changes seeds, previous campaign scripts, or historical outputs.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path

REL='A006_FORCEQUAL_PATCH_v0.5.0b'
SRC=Path(__file__).resolve().parent
MANAGED_BEGIN='% >>> A006_FORCEQUAL_v050b_ALIASES_BEGIN'
MANAGED_END='% <<< A006_FORCEQUAL_v050b_ALIASES_END'
BRIDGE='if /I "%~1"=="FORCEQUAL" goto forcequal'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def check(root):
 runner=root/'run_all.cmd';rc=root/'knotplotrc.kps';src=root/'tools/selection_v050.py'
 seed=root/'Output/v050/geometry/LINK_5_5_6_BALANCED_N1024_ORIG_CPFIXED61.xyz'
 for p in (runner,rc,src,seed):
  if not p.is_file():raise RuntimeError('Target is not v0.5.0a or required file missing: '+str(p))
 st=runner.read_text(encoding='utf-8-sig');rct=rc.read_text(encoding='utf-8-sig')
 if 'A006 v0.5.0' not in st or 'selection_v050.py' not in st:
  raise RuntimeError('run_all.cmd lacks expected v0.5.0 release markers')
 if BRIDGE in st or MANAGED_BEGIN in rct or (root/'tools/force_qualification_v050b.py').exists():
  raise RuntimeError('Already installed or partial installation: do not overwrite')
 if (root/'patch_backups/v050b_FORCEQUAL').exists():raise RuntimeError('Existing patch backup; check before retry')
 return {'root':str(root),'run_all_sha256':sha(runner),'knotplotrc_sha256':sha(rc),'source_seed_sha256':sha(seed)}

def aliased():
 out=[MANAGED_BEGIN]
 for name,short in [('BEND_OFF','fqB0'),('BEND_1','fqB1'),('BEND_10','fqB10'),('BEND_100','fqB100'),('MECH_ONLY','fqM'),('ELEC_ONLY','fqE')]:
  out.append(f'alias {short} "read Output/qualification_v050b/scripts/FQ_{name}.kps"')
 out.append(MANAGED_END)
 return '\n'.join(out)+'\n'

def install(root):
 import shutil
 info=check(root)
 r=root/'run_all.cmd';rc=root/'knotplotrc.kps'
 rb=r.read_text(encoding='utf-8-sig');rs=rc.read_text(encoding='utf-8-sig')
 if not rb.startswith('@echo off') or ':usage' not in rb:raise RuntimeError('Unexpected dispatcher layout')
 # Do not silently replace unrelated user aliases.
 for short in ('fqB0','fqB1','fqB10','fqB100','fqM','fqE'):
  import re
  if re.search(r'^\s*alias\s+'+short+r'\s',rs,flags=re.M|re.I):raise RuntimeError('Alias collision: '+short)
 backup=root/'patch_backups/v050b_FORCEQUAL'; backup.mkdir(parents=True,exist_ok=False)
 shutil.copy2(r,backup/'run_all.cmd');shutil.copy2(rc,backup/'knotplotrc.kps')
 (root/'tools').mkdir(exist_ok=True)
 shutil.copy2(SRC/'tools/force_qualification_v050b.py',root/'tools/force_qualification_v050b.py')
 inserted=rb.replace('cd /d "%~dp0"','cd /d "%~dp0"\n'+BRIDGE,1)
 block=':forcequal\npy -3 tools\\force_qualification_v050b.py %2 %3 %4 %5 %6 %7 %8 %9\nexit /b %errorlevel%\n'
 inserted=inserted.replace(':usage\n',block+':usage\n',1)
 r.write_text(inserted,encoding='utf-8',newline='\n')
 rc.write_text(rs.rstrip()+'\n\n'+aliased(),encoding='utf-8',newline='\n')
 manifest={**info,'version':'0.5.0b','status':'INSTALLED','added_dispatch':'FORCEQUAL',
  'added_aliases':['fqB0','fqB1','fqB10','fqB100','fqM','fqE'],
  'rollback_files':'patch_backups/v050b_FORCEQUAL',
  'installed_run_all_sha256':sha(r),'installed_knotplotrc_sha256':sha(rc),
  'warning':'Existing v0.5.0a campaigns include unsupported /s CSV; NOT patched by this qualification add-on'}
 (backup/'PATCH_INSTALLED.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 # Prepare exactly reproducible six scripts, no runtime XYZ and no fake CSV.
 sys.path.insert(0,str(root/'tools'))
 from force_qualification_v050b import selftest,prepare
 selftest(root);prepare(root)
 print('PATCH INSTALLED: run_all.cmd FORCEQUAL TEST/PLAN/BUILD/ANALYZE; aliases fqB0 fqB1 fqB10 fqB100 fqM fqE')

def rollback(root):
 import shutil
 backup=root/'patch_backups/v050b_FORCEQUAL'
 for file in ('run_all.cmd','knotplotrc.kps'):
  if not (backup/file).is_file():raise RuntimeError('Backup missing: '+file)
 manifest=json.loads((backup/'PATCH_INSTALLED.json').read_text(encoding='utf-8'))
 if sha(root/'run_all.cmd')!=manifest['installed_run_all_sha256'] or sha(root/'knotplotrc.kps')!=manifest['installed_knotplotrc_sha256']:
  raise RuntimeError('Current dispatcher/RC changed since patch; refusing destructive rollback')
 if BRIDGE not in (root/'run_all.cmd').read_text(encoding='utf-8-sig'):
  raise RuntimeError('Current dispatcher does not have patch marker; refusing rollback')
 if MANAGED_BEGIN not in (root/'knotplotrc.kps').read_text(encoding='utf-8-sig'):
  raise RuntimeError('Current rc lacks patch marker; refusing rollback')
 shutil.copy2(backup/'run_all.cmd',root/'run_all.cmd')
 shutil.copy2(backup/'knotplotrc.kps',root/'knotplotrc.kps')
 # Never delete generated results or tests in rollback; simply disconnect.
 print('ROLLBACK: run_all and knotplotrc restored; qualification files preserved, never erased')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,required=True)
 g=ap.add_mutually_exclusive_group(required=True)
 g.add_argument('--check',action='store_true');g.add_argument('--apply',action='store_true');g.add_argument('--rollback',action='store_true')
 a=ap.parse_args();root=a.base.resolve()
 if a.check:print('CHECK ONLY PASS:',json.dumps(check(root),indent=2))
 if a.apply:install(root)
 if a.rollback:rollback(root)
if __name__=='__main__':
 try:main()
 except Exception as e:print('PATCH REFUSED:',e,file=sys.stderr);sys.exit(2)
