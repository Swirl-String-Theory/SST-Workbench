#!/usr/bin/env python3
"""Strict KnotPlot XYZ v0.4.2a: 3 numeric-only blocks, exactly two empty separator lines.

KnotPlot's `coords` snapshots may have component labels; --normalize-raw is explicit,
non-destructive and writes to a DIFFERENT destination. It never changes originals.
"""
import argparse, re, sys, tempfile
from pathlib import Path

NUMBER = re.compile(r'[+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\Z')
LABEL = re.compile(r'(?:Component|Comp)\s*#?\s*\d+\s*:', re.I)

def validate_text(text, n=None):
    if '\r' in text: raise ValueError('Only LF newline is permitted')
    if not text.endswith('\n'):raise ValueError('Must end with single LF')
    if text.endswith('\n\n'):raise ValueError('Trailing blank component')
    lines=text.splitlines()
    blank=[i for i,line in enumerate(lines) if line=='']
    if len(blank)!=2:raise ValueError('Expected exactly two blank separator lines')
    blocks=text.split('\n\n')
    if len(blocks)!=3:raise ValueError('Expected 3 blocks')
    lengths=[]
    for block in blocks:
        rows=block.splitlines(); lengths.append(len(rows))
        for row in rows:
            parts=row.split(' ')
            if len(parts)!=3 or not all(NUMBER.fullmatch(v) for v in parts):
                raise ValueError('Non-numeric XYZ row or non-canonical spacing: '+repr(row))
    # Different counts are allowed; each component is an independent closed polygon.
    if any(x < 1 for x in lengths):raise ValueError('Empty component')
    if n is not None:
        expected=[n]*3 if isinstance(n,int) else list(n)
        if lengths!=expected:raise ValueError(f'Expected {expected}, got {lengths}')
    return lengths

def assert_strict_xyz(path,n=None):
    return validate_text(Path(path).read_text(encoding='ascii'),n)

def normalize_knotplot_coords(path, destination, beads=None):
    path=Path(path);destination=Path(destination)
    if path.resolve()==destination.resolve():raise ValueError('Refuse in-place normalization')
    if destination.exists():raise FileExistsError('Destination already exists: '+str(destination))
    contents=path.read_text(encoding='utf-8-sig')
    groups=[];group=[]
    for line in contents.splitlines():
        s=line.strip()
        if not s or LABEL.fullmatch(s):
            if group:
                groups.append(group);group=[]
            continue
        values=s.split()
        if len(values)!=3 or not all(NUMBER.fullmatch(v) for v in values):
            raise ValueError('Unexpected row: '+repr(s))
        group.append(' '.join(values))
    if group:groups.append(group)
    if len(groups)!=3:raise ValueError('Expected exactly 3 components, got '+str(len(groups)))
    output='\n\n'.join('\n'.join(group) for group in groups)+'\n'
    validate_text(output,beads)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(output,encoding='ascii',newline='\n')
    return destination

def selftest():
    row='1.0 2.0 3.0'
    raw=('Component 0:\n'+row+'\n\n'+'Component 1:\n'+row+'\n\n'+'Component 2:\n'+row+'\n')
    with tempfile.TemporaryDirectory() as d:
        src=Path(d)/'raw.txt';dst=Path(d)/'normalized.xyz';src.write_text(raw)
        normalize_knotplot_coords(src,dst,1)
        assert assert_strict_xyz(dst,1)==[1,1,1]
        for bad in ('Component 0:\n','1 2 3\n1 2 3\n'):
            try:validate_text(bad)
            except ValueError:pass
            else:raise AssertionError('validator accepts wrong format')
    print('PASS: numeric-only 3-block XYZ, header removal to distinct output, strict separators')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--validate',type=Path);p.add_argument('--normalize-raw',type=Path);p.add_argument('--output',type=Path);p.add_argument('--n',type=int)
    x=p.parse_args()
    if x.test:selftest()
    elif x.validate:print('PASS:',x.validate,assert_strict_xyz(x.validate,x.n))
    elif x.normalize_raw:
        if x.output is None:p.error('--output required')
        print('NORMALIZED:',normalize_knotplot_coords(x.normalize_raw,x.output,x.n))
    else:p.error('specify --test, --validate or --normalize-raw')

if __name__=='__main__':main()
