#!/usr/bin/env python3
"""Make a non-mutating, versioned copy of E010 v0.3.1 then install dynamics patch."""
from pathlib import Path
import argparse,shutil,sys

def main():
 p=argparse.ArgumentParser();p.add_argument('--e010-v031',required=True);p.add_argument('--target',required=True);a=p.parse_args()
 src=Path(a.e010_v031).resolve(); dst=Path(a.target).resolve(); patch=Path(__file__).resolve().parent
 if not(src/'pklsa_builder'/'gilbert.py').is_file() or not(src/'pklsa_builder'/'io_geometry.py').is_file():
  raise SystemExit('REJECTED: the original E010-v0.3.1 pklsa_builder source is required')
 if dst.exists():raise SystemExit('REJECTED: destination already exists; no overwrite allowed')
 if dst==src or src in dst.parents or dst in src.parents:raise SystemExit('REJECTED: target must be a separate sibling directory')
 # Avoid duplicating results/data/vendor trees; original remains untouched.
 ignore=shutil.ignore_patterns('.venv','venv','build','dist','__pycache__','.pytest_cache','*.egg-info',
  '*-outputs','*-outputs.zip','*.pyd','.git','.cache','*.log')
 shutil.copytree(src,dst,ignore=ignore)
 shutil.copy2(patch/'overlay'/'pklsa_builder'/'dynamics_ready.py',dst/'pklsa_builder'/'dynamics_ready.py')
 for f in ('pklsa_dynamics_v032.py','run_dynamics_v032.cmd','VERSIONED_EXTENSION_README.md', 'run_all_v032.cmd', 'DYNAMICS_EXTENSION_RELEASE.json', 'emit_framework_v110_ledger.py'):
  shutil.copy2(patch/f,dst/f)
 (dst/'tests').mkdir(exist_ok=True)
 shutil.copy2(patch/'tests'/'test_dynamics_v032.py',dst/'tests'/'test_dynamics_v032.py')
 if (dst/'run_all.cmd').is_file():
  (dst/'run_all.cmd').rename(dst/'run_all_E010_v031.cmd')
 shutil.copy2(patch/'run_all_v032.cmd',dst/'run_all.cmd')
 print('Created',dst,'without modifying',src)
 print('Run run_dynamics_v032.cmd BASIC then FULL in new v0.3.2 source tree')
if __name__=='__main__':main()
