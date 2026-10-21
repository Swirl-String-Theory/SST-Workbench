#!/usr/bin/env python3
import argparse,sys, tempfile,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from metrics_native import render_commands
from analyze_borromean import static_measure,read_native
from build_whole import write_xyz

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);a=ap.parse_args()
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); t=np.arange(100)*2*np.pi/100
        q=[np.column_stack((np.cos(t)+k*4,np.sin(t),np.zeros(len(t)))) for k in range(3)]
        path=root/'3.xyz';write_xyz(path,q)
        rows,links=static_measure(path)
        assert len(rows)==3 and all(.98<x['closure_over_median']<1.02 for x in rows)
        assert all(np.isfinite(x['kappa_max']) for x in rows)
        assert path.read_text().count('\n\n')==2
        commands=render_commands(path,Path('output/borromean/metrics/test.csv'),'off')
        assert not any(line.lower().startswith(('load ','coords ','save ')) for line in commands.splitlines())
        assert 'data open ' in commands and 'data close' in commands
        ext=render_commands(path,Path('output/borromean/metrics/test_extended.csv'),'off',extended=True)
        assert 'data format "/I,/W,/F"' in ext and 'acn' in ext
        assert [int(x.split()[1]) for x in commands.splitlines() if x.startswith('ago ') ]==[1,7,24,96,384,488,1000,2000,4000]
        csvp=root/'x.csv';csvp.write_text('iteration,nbeads,length,rog,safe\n0,300,10,2,1\n1,300,9,1.9,1\n')
        assert len(read_native(csvp))==2
        csvp.write_text('iteration,nbeads,length,rog,safe\n0,300,10,2,1\n0,300,9,1.9,1\n')
        try:read_native(csvp)
        except ValueError:pass
        else:raise AssertionError('duplicate iteration accepted')
    base=Path(a.root)
    assert (base/'extensions/borromean/whole/SCALE_PATCH_RECEIPT.json').exists()
    print('PASS: static component metrics, numeric-only XYZ, KnotPlot data-script increments, no LOAD/KPC, CSV audit')
    print('RUNTIME NOT EXECUTED; MILNOR mu123 UNRESOLVED')
if __name__=='__main__':main()
