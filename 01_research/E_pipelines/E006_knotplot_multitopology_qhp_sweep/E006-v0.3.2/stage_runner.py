from __future__ import annotations
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path(__file__).resolve().parent;P=json.loads((ROOT/"stage_panels.json").read_text())
QMIN="42.0586,1.43298,6.215";QMAX="44.3970,1.47040,6.320"
def main():
    if len(sys.argv)<2 or sys.argv[1] not in P:
        print("Usage: stage_runner.py <stage1_science|stage2_torus|stage3_twist|stage4_rest> [sweep overrides]");return 2
    name=sys.argv[1];extra=sys.argv[2:];p=P[name]
    args=[str(ROOT/".venv/Scripts/python.exe"),str(ROOT/"sweep.py"),f"--qhp-min={QMIN}",f"--qhp-max={QMAX}","--qhp-mode=line",f"--scripts={p['default_scripts']}",f"--max-ago={p['default_max_ago']}","--progress-every=30","--beads-per-component=300",f"--name={name}"]
    if p['knots']:args.append('--knots='+','.join(p['knots']))
    if p['links']:args.append('--links='+','.join(p['links']))
    if p['torus']:args.append('--torus='+','.join(p['torus']))
    args+=extra
    print('='*72);print(p['title']);print(p['purpose']);print('Topologies:',len(p['knots'])+len(p['links'])+len(p['torus']));print('Defaults: scripts=',p['default_scripts'],' max-ago=',p['default_max_ago']);print('='*72,flush=True)
    return subprocess.call(args,cwd=ROOT)
if __name__=='__main__':raise SystemExit(main())
