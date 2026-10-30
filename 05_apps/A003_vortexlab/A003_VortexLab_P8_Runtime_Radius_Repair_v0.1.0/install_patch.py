#!/usr/bin/env python3
"""Fail-closed, no-overwrite patch for exact A003 29-10 sources."""
from pathlib import Path
import argparse,hashlib,json,shutil,sys,datetime
HERE=Path(__file__).resolve().parent
MAN=json.loads((HERE/'PATCH_MANIFEST.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--target',required=True,help='Root A003_vortexlab folder containing package.json')
 p.add_argument('--apply',action='store_true',help='Actually apply after verification')
 args=p.parse_args()
 root=Path(args.target).resolve()
 if not (root/'package.json').is_file() or not (root/'apps/web/src/legacy/vortexlab-runtime.js').exists():
  print('REFUSED: not A003 root',file=sys.stderr);return 2
 for row in MAN['files']:
  f=root/row['path'];payload=HERE/'payload'/row['path']
  if not f.is_file() or sha(f)!=row['original_sha256'] or sha(payload)!=row['patched_sha256']:
   print('REFUSED: missing/modified file '+str(f),file=sys.stderr);return 3
 print('PREFLIGHT PASS: all 4 exact source versions match (no modification yet).')
 if not args.apply:
  print('Add --apply to install.');return 0
 backup=root/'.P8_runtime_radius_backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
 for row in MAN['files']:
  f=root/row['path'];b=backup/row['path'];b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,b)
 for row in MAN['files']:
  f=root/row['path'];tmp=f.with_name(f.name+'.p8tmp');shutil.copy2(HERE/'payload'/row['path'],tmp);tmp.replace(f)
 assert all(sha(root/row['path'])==row['patched_sha256'] for row in MAN['files'])
 print('APPLIED P8 repair; rollback originals in '+str(backup))
 print('No solver time stepping, core regularization, or contact guards changed.')
 return 0
if __name__=='__main__':raise SystemExit(main())
