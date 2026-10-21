#!/usr/bin/env python3
"""Safely install A006 v0.4.3a beadlimit hotfix on existing v0.4.3."""
from __future__ import annotations
import argparse,hashlib,json,os,shutil
from pathlib import Path

ORIGINAL_SHA256 = 'd325b883aa60fca316ea11f8a4936cd38146a5fa1f172e0b44c02e90043a4c64'
PATCHDIR = Path(__file__).resolve().parent
NEW_SOURCE = PATCHDIR/'tools'/'selection_v043.py'
RECEIPT_NAME = 'BEADLIMIT_PATCH_RECEIPT_v043a.json'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def check(base):
 base=Path(base).resolve()
 runner=base/'tools'/'selection_v043.py'
 cmd=base/'run_all.cmd'
 if not cmd.is_file() or not runner.is_file():
  raise RuntimeError('A006 v0.4.3 is not installed (run_all.cmd or selection_v043.py missing)')
 if b'A006_SELECT_DISPATCH_v043' not in cmd.read_bytes():
  raise RuntimeError('v0.4.3 selector dispatcher not found; target not verified')
 if sha(runner)!=ORIGINAL_SHA256:
  raise RuntimeError('selection_v043.py is not the untouched v0.4.3 baseline; refuse overwrite')
 if not NEW_SOURCE.is_file():raise RuntimeError('Hotfix source missing')
 backup=base/'patch_backups'/'selection_v043a_beadlimit'
 if backup.exists():raise RuntimeError('v0.4.3a backup/receipt folder already exists; refuse repeat install')
 return {'status':'CHECK_PASS','root':str(base),'source_sha256':sha(runner),
         'replacement_sha256':sha(NEW_SOURCE),'run_all_cmd_unchanged':True,
         'only_modified_file':'tools/selection_v043.py'}

def apply(base):
 report=check(base);base=Path(base).resolve()
 runner=base/'tools'/'selection_v043.py'
 backup=base/'patch_backups'/'selection_v043a_beadlimit'
 backup.mkdir(parents=True,exist_ok=False)
 old=backup/'selection_v043_before_v043a.py'
 old.write_bytes(runner.read_bytes())
 tmp=runner.with_name('selection_v043.beaddlimit.tmp.py')
 try:
  shutil.copy2(NEW_SOURCE,tmp)
  os.replace(tmp,runner)
  if sha(runner)!=report['replacement_sha256']:
   raise RuntimeError('File digest verification failed')
  receipt={'status':'INSTALLED','version':'v0.4.3a','source_sha256':sha(old),
           'patched_sha256':sha(runner),'run_all_cmd_unchanged':True,
           'path':'tools/selection_v043.py','backup':str(old.relative_to(base)),
           'scientific_status':'KnotPlot runtime NOT TESTED; beadlimit infrastructure only'}
  (backup/RECEIPT_NAME).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
  return receipt
 except Exception:
  runner.write_bytes(old.read_bytes())
  tmp.unlink(missing_ok=True)
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description='A006 v0.4.3a beadlimit hotfix')
 p.add_argument('--base',required=True,type=Path)
 mode=p.add_mutually_exclusive_group(required=True)
 mode.add_argument('--check',action='store_true')
 mode.add_argument('--apply',action='store_true')
 args=p.parse_args()
 try: print(json.dumps(check(args.base) if args.check else apply(args.base),indent=2))
 except Exception as e:
  print('PATCH BLOCKED:',e);raise SystemExit(2)
