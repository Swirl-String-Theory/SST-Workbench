"""Explicit PILOT entry point. Does not emulate frozen SST framework's FREEZE/REVEAL/CERTIFY."""
import subprocess, sys, os
from pathlib import Path
root=Path(__file__).resolve().parent
mode=sys.argv[1].upper() if len(sys.argv)>1 else 'PILOT'
if mode=='SELFTEST':
    raise SystemExit(subprocess.call([sys.executable,'-m','pytest','-q',str(root/'tests')],cwd=root))
if mode=='PILOT':
    raise SystemExit(subprocess.call([sys.executable,str(root/'src'/'pilot.py')],cwd=root))
raise SystemExit('Only PILOT and SELFTEST supported. Formal v1.0.7 FREEZE/CERTIFY/REVEAL must use actual generated framework instance.')
