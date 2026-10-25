#!/usr/bin/env python3
"""Non-destructive A006 v0.5.0f installer; never overwrites existing gallery files."""
import argparse, shutil, sys
from pathlib import Path

src=Path(__file__).resolve().parent
ap=argparse.ArgumentParser()
ap.add_argument('--target',required=True,help='Existing A006-v0.5.0 base directory')
grp=ap.add_mutually_exclusive_group()
grp.add_argument('--dry-run',action='store_true')
grp.add_argument('--apply',action='store_true')
ns=ap.parse_args()
target=Path(ns.target).resolve()
if not target.is_dir(): sys.exit(f'ERROR: existing target folder not found: {target}')
dest=target/'tikz_hobby_v050f'
if dest.exists():sys.exit(f'BLOCKED: sidecar already exists; refusing overwrite: {dest}')
if target==src or src in target.parents:sys.exit('BLOCKED: cannot install to package root')
print(f'Source: {src}\nTarget: {dest}\nNon-destructive sidecar only (existing seeds remain unchanged)')
if not ns.apply:
 print('DRY RUN ONLY: no changes made. Add --apply to copy sidecar.');sys.exit(0)
try:
 shutil.copytree(src,dest,ignore=shutil.ignore_patterns('_tex_build','__pycache__','*.pdf','*.svg','*.log','*.aux'))
except Exception:
 shutil.rmtree(dest,ignore_errors=True)
 raise
print('CREATED:',dest)
