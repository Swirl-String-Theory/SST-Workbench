from __future__ import annotations
import argparse
from pathlib import Path
from . import blind,reveal

def main():
    p=argparse.ArgumentParser(); p.add_argument('--mode',choices=['blind','reveal','all'],default='all'); p.add_argument('--root',default='.'); p.add_argument('--outputs',default='outputs'); a=p.parse_args()
    root=Path(a.root).resolve(); out=Path(a.outputs); out=out if out.is_absolute() else root/out
    if a.mode in ('blind','all'): blind.run(root,out)
    if a.mode in ('reveal','all'): reveal.run(root,out)
if __name__=='__main__': main()
