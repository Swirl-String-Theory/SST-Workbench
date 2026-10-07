from pathlib import Path
import argparse,json
from sst_falsifier.provenance import find_release_contamination
p=argparse.ArgumentParser();p.add_argument("root",nargs="?",default=".");a=p.parse_args();hits=find_release_contamination(Path(a.root));print(json.dumps(hits,indent=2));raise SystemExit(1 if hits else 0)
