from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from sst_falsifier_framework.outputs import pack_outputs, default_output_dir
p=argparse.ArgumentParser(); p.add_argument('--output',default=str(default_output_dir(ROOT))); a=p.parse_args()
print('\n'.join(pack_outputs(Path(a.output),ROOT.name,ROOT.parent)))
