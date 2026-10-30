from __future__ import annotations
import argparse
from .runner import run_mode

def main():
    p=argparse.ArgumentParser(); p.add_argument("instance_root"); p.add_argument("mode",choices=["SELFTEST","FREEZE","BASIC","FULL","CERTIFY","REVEAL"])
    a=p.parse_args(); raise SystemExit(run_mode(a.instance_root,a.mode))
if __name__=="__main__": main()
