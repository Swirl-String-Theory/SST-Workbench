from pathlib import Path
import argparse, json
from sst_falsifier_core.blind import scan_tree
p=argparse.ArgumentParser(); p.add_argument("root",nargs="?",default="."); p.add_argument("--terms",nargs="*",default=[])
a=p.parse_args(); hits=scan_tree(a.root,forbidden=tuple(a.terms) if a.terms else ()) if a.terms else []
print(json.dumps({"ok":not hits,"hits":hits},indent=2)); raise SystemExit(1 if hits else 0)
