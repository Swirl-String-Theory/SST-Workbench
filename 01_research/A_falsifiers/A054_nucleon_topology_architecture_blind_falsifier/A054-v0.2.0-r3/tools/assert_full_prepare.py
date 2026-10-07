from __future__ import annotations
import json, sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: assert_full_prepare.py <campaign-dir>')
p=Path(sys.argv[1])/'PREPARE_STATUS.json'
if not p.is_file():
    print(f'ERROR: missing {p}', file=sys.stderr); raise SystemExit(20)
obj=json.loads(p.read_text(encoding='utf-8'))
if obj.get('status') != 'PREPARED_FULL':
    up=Path(sys.argv[1])/'UPSTREAM_PLAN.json'
    print('ERROR: full-factorial preparation was not achieved.', file=sys.stderr)
    print(json.dumps(obj,indent=2), file=sys.stderr)
    if up.is_file():
        print('UPSTREAM_PLAN:', file=sys.stderr)
        print(up.read_text(encoding='utf-8'), file=sys.stderr)
    print('Use run_controls.cmd only if you intentionally want the three analytic control diagnostics.', file=sys.stderr)
    raise SystemExit(20)
print('PREPARED_FULL confirmed.')
