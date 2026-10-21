"""Inspect KnotPlot target/Start-in without executing KnotPlot or writing output."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.shortcut_runtime import resolve_launcher

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['CHECK_SHORTCUT'])
    parser.add_argument('--exe',type=Path,required=True)
    parser.add_argument('--workdir',type=Path)
    args=parser.parse_args()
    try:
        launch=resolve_launcher(args.exe,workdir_override=args.workdir)
    except Exception as exc:
        print('A058 CHECK_SHORTCUT FAIL-CLOSED:',type(exc).__name__,str(exc),file=sys.stderr)
        return 2
    print(json.dumps({'status':'LAUNCH_PATHS_RESOLVED_ONLY','exe':str(launch.executable),
        'shortcut':str(launch.shortcut) if launch.shortcut else None,
        'workdir':str(launch.workdir),'workdir_source':launch.workdir_source,
        'shortcut_arguments':launch.shortcut_args,
        'native_KnotPlot_executed':False},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
