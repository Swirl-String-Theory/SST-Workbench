#!/usr/bin/env python3
"""Repair ONLY the ForceGrid analyzer's Windows CRLF script-digest check.

Never changes PLAN.json, checkpoint XYZ, native CSV, KPS scripts, aliases or dispatcher.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys,tempfile
from pathlib import Path

REL=Path('tools/force_grid_v050c.py')
PLAN=Path('Output/qualification_v050c/PLAN.json')
BACKUP=Path('patch_backups/A006_v0.5.0c3_analyzer_fix')
OLD_LINE=b"if sha_file(script)!=expected['script_sha256']:"
NEW_LINE=b"if sha_script(script)!=expected['script_sha256']:"
OLD_DEF=b'def sha_file(p):return sha_bytes(Path(p).read_bytes())'
NEW_DEF=b'def sha_script(p):\n raw=Path(p).read_bytes()\n return sha_bytes(raw.replace(b"\\r\\n",b"\\n"))'

def sha(data):return hashlib.sha256(data).hexdigest()
def digest_script(raw):return sha(raw.replace(b'\r\n',b'\n'))
def patched(data):
 if data.count(OLD_LINE)!=1 or data.count(OLD_DEF)!=1:
  raise RuntimeError('Source does not match expected v0.5.0c analyzer: refuse unsafe rewrite')
 nl=b'\r\n' if b'\r\n' in data else b'\n'
 insert=NEW_DEF.replace(b'\n',nl)
 data=data.replace(OLD_DEF,OLD_DEF+nl+insert,1)
 data=data.replace(OLD_LINE,NEW_LINE,1)
 return data

def verify_plan(root):
 path=root/PLAN
 if not path.exists():return {'plan':'MISSING','scripts_checked':0}
 plan=json.loads(path.read_text(encoding='utf-8'))
 scripts=plan.get('arms',{})
 failures=[]
 for name,arm in scripts.items():
  p=root/arm['script']
  if not p.is_file():failures.append(f'{name}:MISSING');continue
  if digest_script(p.read_bytes())!=arm['script_sha256']:failures.append(f'{name}:CONTENT_MISMATCH')
 if failures:raise RuntimeError('Real script or manifest mismatch: '+', '.join(failures))
 return {'plan':'VALID','scripts_checked':len(scripts),'line_endings':'CANONICAL_LF_HASH'}

def atomically_write(path,data):
 fd,name=tempfile.mkstemp(dir=path.parent,prefix='.forcegrid_c3_',suffix='.tmp')
 try:
  with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)

def run(root,action):
 target=root/REL
 if not target.is_file():raise RuntimeError('ForceGrid module missing: '+str(target))
 original=target.read_bytes()
 backupdir=root/BACKUP; manifestfile=backupdir/'manifest.json';backupfile=backupdir/'force_grid_v050c.py.before'
 if action=='--rollback':
  if not manifestfile.is_file() or not backupfile.is_file():raise RuntimeError('No v0.5.0c3 backup exists')
  m=json.loads(manifestfile.read_text('utf-8'))
  if sha(original)!=m['patched_sha256']:raise RuntimeError('Analyzer changed after patch: rollback refused')
  before=backupfile.read_bytes()
  if sha(before)!=m['original_sha256']:raise RuntimeError('Backup digest mismatch')
  atomically_write(target,before)
  print('ROLLBACK PASS: original analyzer restored; all data untouched');return
 plan=verify_plan(root)
 if NEW_LINE in original and OLD_LINE not in original:
  if original.count(b'def sha_script(p):')!=1:raise RuntimeError('Unexpected partially patched module')
  print('ALREADY PATCHED:',json.dumps(plan));return
 updated=patched(original)
 print('CHECK PASS:',json.dumps({'source_sha256':sha(original),'patched_sha256':sha(updated),**plan}))
 if action=='--check':return
 if backupdir.exists():
  if not manifestfile.is_file() or not backupfile.is_file():raise RuntimeError('Backup directory incomplete; refusing changes')
  old=json.loads(manifestfile.read_text('utf-8'))
  if old['original_sha256']!=sha(original):raise RuntimeError('Backup mismatch; refusing patch')
  if sha(backupfile.read_bytes())!=sha(original):raise RuntimeError('Backup content mismatch')
 else:
  backupdir.mkdir(parents=True,exist_ok=False)
  atomically_write(backupfile,original)
  atomically_write(manifestfile,json.dumps({'original_sha256':sha(original),'patched_sha256':sha(updated),'scope':'ONLY analyzer script-digest check'},indent=2).encode('utf-8')+b'\n')
 atomically_write(target,updated)
 if sha(target.read_bytes())!=sha(updated):raise RuntimeError('Patched module read-back mismatch')
 print('APPLIED: analyzer now compares SHA256 over CRLF-normalized LF scripts.')
 print('NEXT: run_all.cmd FORCEGRID ANALYZE')

if __name__=='__main__':
 a=argparse.ArgumentParser()
 a.add_argument('--base',type=Path,default=Path('.'))
 g=a.add_mutually_exclusive_group(required=True)
 g.add_argument('--check',action='store_true')
 g.add_argument('--apply',action='store_true')
 g.add_argument('--rollback',action='store_true')
 args=a.parse_args()
 action='--apply' if args.apply else '--check' if args.check else '--rollback'
 try:run(args.base.resolve(),action)
 except (RuntimeError,OSError,KeyError,ValueError,json.JSONDecodeError) as e:
  print('REPAIR REFUSED:',e,file=sys.stderr);sys.exit(2)
