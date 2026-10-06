from pathlib import Path
import json, argparse
p=argparse.ArgumentParser(); p.add_argument('--blind',required=True); p.add_argument('--snapshot',required=True); p.add_argument('--out',required=True); a=p.parse_args()
blind=json.loads(Path(a.blind).read_text()); snap=json.loads(Path(a.snapshot).read_text())
out={'schema':'A051_REVEAL_1.0','blind_verdict':blind.get('verdict'),'physics_verdict':blind.get('physics_verdict'),'upstream_sources':{k:{'drive_file_id':v['drive_file_id'],'extract':v['extract']} for k,v in snap['sources'].items()},'note':'Reveal maps immutable blind results to named upstream context; no blind metric is recomputed.'}
Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
