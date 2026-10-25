"""Backward-compatible v0.1 commands plus independent v0.2 commands."""
import sys,unittest
from pathlib import Path
from .__main__ import cli as old_cli
from .euler_qualification import main as euler_main
from .native_qualification import main as native_main

def main():
    args=sys.argv[1:]
    if args and args[0].upper()=='TEST':
        tests=Path(__file__).resolve().parents[1]/'tests'
        suite=unittest.defaultTestLoader.discover(str(tests),pattern='test_*.py')
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 2
    if args and args[0].upper()=='EULER':return euler_main(args[1:])
    if args and args[0].upper()=='NATIVE':return native_main(args[1:])
    if args and args[0].upper()=='DEMO':
        root=Path(__file__).resolve().parents[1]
        dest=str(root/'Output'/'VCCR_v0.2.0')
        code=old_cli(['analytic','--out',dest])
        if code:return code
        code=old_cli(['geometry']+[str(x) for x in sorted((root/'examples').glob('*.xyz'))]+['--out',dest])
        if code:return code
        return euler_main(['--out',str(root/'Output'/'VCCR_v0.2.0'/'euler'),'--case','both'])
    return old_cli(args)
if __name__=='__main__':raise SystemExit(main())
