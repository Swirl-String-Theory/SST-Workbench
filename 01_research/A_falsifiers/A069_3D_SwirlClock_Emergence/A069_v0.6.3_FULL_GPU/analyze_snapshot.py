#!/usr/bin/env python3
"""Postprocess saved XPU GP field in a separate process; diagnostic, not knot proof."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from a069_v061.subgrid import subgrid_filaments,spectral_grid_shift
from a069_v061.projection_topology_v062 import numerical_projection_audit
from gp_full_xpu import sha256,json_exclusive

def stripped(field,box,offsets=()):
    # Complex64 GPU fields require float64 link-angle arithmetic to satisfy the
    # original strict 3e-11 integer-winding closure; do not loosen its tolerance.
    field=np.asarray(field,dtype=np.complex128)
    r=subgrid_filaments(field,box)
    for c in r['components']:
        if c['simple_oriented_cycle']:
            c['projection_diagnostic']=numerical_projection_audit(c['subgrid_polyline'])
        else:c['projection_diagnostic']={'status':'UNRESOLVED_NON_SIMPLE_GRAPH','topology_certified':False}
        c.pop('subgrid_polyline',None)
    shift_info=[]
    for sh in offsets:
        z=spectral_grid_shift(field,box,sh)
        d=subgrid_filaments(z,box)
        shift_info.append({'offset_cells':sh,'components':d['components_count'],
                           'simple_cycles':sum(int(x['simple_oriented_cycle']) for x in d['components']),
                           'junctions':d['ambiguous_lattice_junctions'],
                           'qualified':d['subgrid_reconstruction_qualified']})
    return r,shift_info

def analyze(path,box=10.,max_n=256,offsets=()):
    p=Path(path)
    if not p.is_file():raise FileNotFoundError(p)
    if p.suffix=='.npz':
        with np.load(p,allow_pickle=False) as z:
            if 'psi' not in z:raise ValueError('missing psi')
            a=np.asarray(z['psi'])
            if 'box' in z:box=float(z['box'])
    elif p.suffix=='.npy':a=np.load(p,mmap_mode='r',allow_pickle=False)
    else:raise ValueError('only .npz or .npy saved GP states are supported')
    if a.ndim!=3 or any(n!=a.shape[0] for n in a.shape):raise ValueError('3D cubic field required')
    n=len(a)
    if n>max_n:raise MemoryError(f'CPU topology analysis N={n} > max_n={max_n}; larger fields need dedicated memory profiling')
    if not np.isfinite(a).all():raise ValueError('invalid nonfinite field')
    r,offset=stripped(a,box,offsets)
    return {'schema':'A069-V063-OFFLINE-SUBGRID-1','input_file':str(p.absolute()),'sha256':sha256(p),
            'n':n,'box':box,'subgrid':r,'offsets':offset,
            'g33':{'status':'PASS' if r['subgrid_reconstruction_qualified'] else 'UNRESOLVED',
                   'qualification':'DIAGNOSTIC_ONLY','execution_status':'EXECUTED'},
            'g34':{'status':'UNRESOLVED','qualification':'UNRESOLVED'},
            'g35':{'status':'UNRESOLVED','qualification':'UNRESOLVED'},
            'claim_guard':'Snapshot Fox determinant and cycles do not establish ambient isotopy over time.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--field',type=Path,required=True)
    p.add_argument('--box',type=float,default=10.)
    p.add_argument('--max-n',type=int,default=256)
    p.add_argument('--offsets',action='store_true',help='two extra spectral subcell-offset comparisons (memory intensive)')
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    shifts=[(.37,.29,.41),(-.23,.19,-.31)] if a.offsets else []
    output=analyze(a.field,a.box,a.max_n,shifts)
    json_exclusive(a.out,output)
    print(json.dumps({'out':str(a.out),'n':output['n'],'components':output['subgrid']['components_count'],
                      'g33':output['g33'],'g34':'UNRESOLVED'},indent=2))
if __name__=='__main__':main()
