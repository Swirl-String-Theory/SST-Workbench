\
from __future__ import annotations
import argparse, json
from pathlib import Path
from .common import OUTPUT_DIR
from .blind import run as run_blind

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("mode",choices=["blind","reveal"])
    ap.add_argument("--config",required=True)
    args=ap.parse_args()
    root=Path.cwd()
    out=root/OUTPUT_DIR
    if args.mode=="blind":
        result=run_blind(root,Path(args.config),out)
    else:
        from .reveal import run as run_reveal
        result=run_reveal(root,Path(args.config),out)
    print(json.dumps({"mode":args.mode,"verdict":result["verdict"],"output":str(out)},indent=2))
if __name__=="__main__": main()
