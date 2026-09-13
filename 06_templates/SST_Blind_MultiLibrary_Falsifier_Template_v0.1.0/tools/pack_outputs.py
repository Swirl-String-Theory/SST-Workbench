from pathlib import Path
import argparse
from sst_falsifier_core.outputs import pack_blind, pack_revealed
p=argparse.ArgumentParser(); p.add_argument("root"); p.add_argument("zip"); p.add_argument("--revealed",action="store_true")
a=p.parse_args(); print(pack_revealed(a.root,a.zip) if a.revealed else pack_blind(a.root,a.zip))
