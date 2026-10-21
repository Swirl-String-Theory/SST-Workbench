#!/usr/bin/env python3
"""Prepare optional KnotPlot *measurement-only* text; never loads geometry.

User opens .xyz directly with KnotPlot.  This script can be copied/pasted
or executed using `read` AFTER the user has loaded geometry. It does not
call `load`, `coords`, `save`, or create KPC/KPT files.
"""
import argparse, json, re
from pathlib import Path

CHECKPOINTS=(0,1,8,32,128,512,1000,2000,4000,8000)
FIELDS='/I,/N,/l,/g,/s'

def find_xyz(root,composition,profile,n_shortest):
    out=Path(root)/'output'/'borromean'
    stem=f'Borromean_{"_".join(composition)}_{profile}_MIN{int(n_shortest):04d}_'
    found=sorted(out.glob(stem+'*_v042d.xyz'))
    if len(found)!=1:
        raise RuntimeError(f'Expected 1 matching v042d XYZ, found {len(found)}: {found}. Use a unique profile/min resolution/scale.')
    return found[0]

def render_commands(xyz, csvpath, tanf, checkpoints=CHECKPOINTS, extended=False):
    checkpoints=tuple(map(int,checkpoints))
    if checkpoints[0]!=0 or any(b<=a for a,b in zip(checkpoints,checkpoints[1:])):
        raise ValueError('Checkpoints must start 0 and increase strictly')
    tf=tanf.lower(); assert tf in ('on','off')
    lines=[f'echo A006 metric-only ({tf}) - LOAD XYZ MANUALLY FIRST',
           f'tanforce = {tf}', 'collision fast',
           f'data open {csvpath.as_posix()}',
           f'data format "{'/I,/W,/F' if extended else FIELDS}"',
           ('data header "iteration,space_writhe,full_linking_data_UNVERIFIED"' if extended else
            'data header "iteration,nbeads,length,rog,safe"')]
    for i,t in enumerate(checkpoints):
        if i:
            lines.append(f'ago {t-checkpoints[i-1]}')
        lines.extend([f'echo CHECKPOINT {t}', 'length','rog','safe','lnknum', 'acn' if extended else 'nop', 'data'])
    lines.append('data close')
    return '\n'.join(lines)+'\n'

def make(root,composition,profile,n_shortest,tanf,extended=False):
    if composition not in ('556','665') or profile not in ('FLAT','SOFT','BALANCED','TIGHT'):
        raise ValueError('Unknown composition/profile')
    xyz=find_xyz(root,composition,profile,n_shortest)
    csvdir=Path(root)/'output'/'borromean'/'metrics';csvdir.mkdir(parents=True,exist_ok=True)
    stem=xyz.stem+'_'+tanf.upper()
    txt=csvdir/(stem+('_EXTENDED_UNVERIFIED_MEASURE_ONLY.txt' if extended else '_MEASURE_ONLY.txt'))
    csvpath=csvdir/(stem+('_EXTENDED_RAW.csv' if extended else '.csv'))
    if txt.exists():
        raise FileExistsError(f'Refuse to overwrite existing measurement script: {txt}')
    rel=csvpath.relative_to(root)
    txt.write_text(render_commands(xyz,rel,tanf,extended=extended),encoding='ascii',newline='\n')
    print('Geometry to load MANUALLY:',xyz.relative_to(root).as_posix())
    print('After loading it, run measurement-only commands from:',txt.relative_to(root).as_posix())
    print('Expected KnotPlot-native CSV:',rel.as_posix())
    print('WARNING: /l,/g,/s may refer to link-wide metrics. Separate XYZ diagnostics handle individual components.')
    return txt

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--composition',choices=['556','665'],required=True)
    ap.add_argument('--profile',choices=['FLAT','SOFT','BALANCED','TIGHT'],required=True)
    ap.add_argument('--n-shortest',type=int,required=True)
    ap.add_argument('--tanf',type=str.lower,choices=['on','off'],required=True)
    ap.add_argument('--extended',action='store_true',help='UNVERIFIED experimental KnotPlot /W and /F raw output')
    a=ap.parse_args();make(a.root.resolve(),a.composition,a.profile,a.n_shortest,a.tanf,a.extended)
