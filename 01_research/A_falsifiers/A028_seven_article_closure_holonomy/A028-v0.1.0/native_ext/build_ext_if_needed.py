from pathlib import Path
import subprocess,sys,os
ROOT=Path(__file__).resolve().parents[1]
try:
    from . import _native  # noqa
    print('[SST7-NATIVE] already built')
except Exception:
    setup=ROOT/'build'/'_setup_native.py'
    print('[SST7-NATIVE] building:',sys.executable,setup)
    subprocess.check_call([sys.executable,str(setup),'build_ext','--inplace'],cwd=ROOT)
    print('[SST7-NATIVE] build complete')
