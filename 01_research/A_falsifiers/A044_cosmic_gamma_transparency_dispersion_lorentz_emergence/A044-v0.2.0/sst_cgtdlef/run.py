from __future__ import annotations
import argparse
from pathlib import Path
from . import blind, reveal


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--config", default="configs/blind_config.json")
    ap.add_argument("--outputs", default="SST_Cosmic_Gamma_Transparency_Dispersion_Lorentz_Emergence_Falsifier_v0.2.0-outputs")
    ap.add_argument("--candidate", default=None)
    args=ap.parse_args()
    root=Path(args.root).resolve(); out=root/args.outputs
    v=blind.run(root, root/args.config, out)
    print("BLIND:",v["verdict"])
    if args.candidate:
        r=reveal.run(root, root/args.candidate, out)
        print("REVEAL:",r["verdict"])

if __name__ == "__main__":
    main()
