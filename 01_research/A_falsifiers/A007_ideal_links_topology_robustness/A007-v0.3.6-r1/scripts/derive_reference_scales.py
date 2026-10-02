#!/usr/bin/env python3
from __future__ import annotations
import argparse, glob, json
from pathlib import Path
import numpy as np

TERMS = ("length", "bending", "tube_repulsion", "neumann")

def main() -> int:
    parser=argparse.ArgumentParser(description="Derive campaign-global median absolute energy baselines.")
    parser.add_argument("campaign_dir")
    args=parser.parse_args()
    values={name:[] for name in TERMS}
    for path in glob.glob(str(Path(args.campaign_dir)/"per_link"/"*.json")):
        data=json.loads(Path(path).read_text(encoding="utf-8"))
        for sector in data["sector_results"]:
            baseline=sector["energy_closure"]["finite_difference"]["baseline_raw"]
            for name in TERMS: values[name].append(abs(float(baseline[name])))
    result={name:float(np.median(rows)) for name,rows in values.items() if rows}
    print(json.dumps(result,indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())
