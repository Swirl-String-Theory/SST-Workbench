#!/usr/bin/env python3
"""Compare KnotPlot ASCII readback to immutable seed at identical bead indices."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from audit_legacy import components

def main():
    a=argparse.ArgumentParser()
    a.add_argument('expected',type=Path)
    a.add_argument('readback',type=Path)
    a.add_argument('--rtol',type=float,default=1e-12)
    a.add_argument('--atol',type=float,default=1e-12)
    z=a.parse_args()
    expected=components(z.expected.read_text())
    observed=components(z.readback.read_text())
    shape_ok=len(expected)==len(observed) and all(a.shape==b.shape for a,b in zip(expected,observed))
    max_abs=(max(float(np.max(np.abs(x-y))) for x,y in zip(expected,observed)) if shape_ok and expected else None)
    good=(shape_ok and all(np.allclose(x,y,rtol=z.rtol,atol=z.atol) for x,y in zip(expected,observed)))
    print(json.dumps({'roundtrip': 'PASS' if good else 'FAIL','same_component_and_bead_counts':shape_ok,
       'maximum_absolute_coordinate_difference':max_abs,'rtol':z.rtol,'atol':z.atol}))
    if not good:sys.exit(1)
if __name__=='__main__':main()
