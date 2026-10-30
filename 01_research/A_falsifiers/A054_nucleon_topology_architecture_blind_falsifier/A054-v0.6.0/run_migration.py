from pathlib import Path
import sys
sys.dont_write_bytecode=True
from a054_state.migration import run
if __name__=='__main__':
 import json
 print(json.dumps(run(Path(__file__).resolve().parent),indent=2))
