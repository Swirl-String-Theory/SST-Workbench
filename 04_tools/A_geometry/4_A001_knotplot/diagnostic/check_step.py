#!/usr/bin/env python3
"""Report displacement for KnotPlot coords snapshots. Does not establish physically correct dynamics."""
import argparse
from pathlib import Path
import numpy as np

def xyz(p):
    data=[]
    for line in p.read_text(errors='replace').splitlines():
        s=line.strip().split()
        if len(s)==3:
            try:data.append([float(x) for x in s]);continue
            except ValueError:pass
    a=np.asarray(data,dtype=float)
    if a.ndim !=2 or a.shape[1]!=3:raise ValueError(f'No XYZ points in {p}')
    return a

def main():
    parser=argparse.ArgumentParser(description='Measure file-to-file bead coordinate displacement, NOT solver certification')
    parser.add_argument('before',type=Path);parser.add_argument('after',type=Path)
    args=parser.parse_args();a=xyz(args.before);b=xyz(args.after)
    if a.shape!=b.shape:raise ValueError(f'Shape mismatch: {a.shape} vs {b.shape}')
    d=np.linalg.norm(b-a,axis=1)
    print('N_BEADS',len(d),'RMS_DISPLACEMENT_COORD_UNITS',float(np.sqrt(np.mean(d*d))),
          'MAX_DISPLACEMENT_COORD_UNITS',float(d.max()))
    if not np.all(np.isfinite(b)):raise ValueError('NONFINITE_COORDINATES: FAIL')
    if np.max(d)==0:print('STATIC: go 1 produced no measurable change (or saved identical positions).')
    else:print('MOVED: KnotPlot coordinates changed; no claim of valid dynamics.')
if __name__=='__main__':main()
