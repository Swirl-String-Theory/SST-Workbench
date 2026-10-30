from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from maxwell_sst_falsifier.framework_v110 import run

if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
