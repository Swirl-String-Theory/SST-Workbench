"""Read-only pin check. Does NOT replace the canonical framework's own runner."""
from pathlib import Path
import json,os,sys
root=Path(os.environ.get('SST_FALSIFIER_FRAMEWORK_ROOT','')).resolve()
freeze=root/'CANONICAL_FREEZE.json'
if not freeze.is_file():
    raise SystemExit(f'MISSING_FRAMEWORK: {freeze}')
obj=json.loads(freeze.read_text(encoding='utf-8'))
if obj.get('version')!='1.0.7' or obj.get('status')!='CANONICAL_FROZEN':
    raise SystemExit('INCOMPATIBLE_OR_UNFROZEN_FRAMEWORK')
if not (root/'sst_falsifier'/'__init__.py').exists():
    raise SystemExit('NO_FRAMEWORK_RUNTIME')
print('Verified framework metadata:',obj['version'],obj['status'])
print('WARNING: A064 science runner is independent pending registered v1.0.7 pipeline integration.')
