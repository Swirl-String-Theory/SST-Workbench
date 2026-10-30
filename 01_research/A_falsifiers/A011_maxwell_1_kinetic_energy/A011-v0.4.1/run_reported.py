from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
WORKBENCH = ROOT.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from maxwell_sst_falsifier.framework_v110 import qualified_framework, verify_protocol
qualified_framework(ROOT)
verify_protocol(ROOT)
pin = json.loads((ROOT / 'REPORT_OUTPUT_CONTRACT.json').read_text(encoding='utf-8'))
binding = WORKBENCH / pin['binding']
if hashlib.sha256(binding.read_bytes()).hexdigest() != pin['binding_sha256']:
    raise RuntimeError('Pinned report/output adapter binding changed; refusing import')
sys.path.insert(0, str(WORKBENCH / '07_scripts/sst_migration'))
from report_output_contract import run

if __name__ == '__main__':
    print(json.dumps(run(ROOT), indent=2))
