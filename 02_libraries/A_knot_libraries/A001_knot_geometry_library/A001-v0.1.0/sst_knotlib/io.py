from __future__ import annotations
from pathlib import Path
import numpy as np


def load_xyz(path):
    path=Path(path)
    arr=np.loadtxt(path,comments='#',delimiter=',' if path.suffix.lower()=='.csv' else None)
    if arr.ndim!=2 or arr.shape[1]<3:
        raise ValueError('expected at least 3 numeric columns')
    return np.asarray(arr[:,:3],float)


def save_xyz(path, points, header='x y z'):
    np.savetxt(path,np.asarray(points,float),fmt='%.17g',header=header)


def save_vect(path, points):
    p=np.asarray(points,float)
    with open(path,'w',encoding='utf-8') as f:
        f.write('VECT\n')
        f.write(f'1 {len(p)} 0\n')
        f.write(f'-{len(p)}\n')
        f.write('0\n')
        for x,y,z in p:
            f.write(f'{x:.17g} {y:.17g} {z:.17g}\n')


def load_vect(path):
    toks=Path(path).read_text(encoding='utf-8',errors='ignore').split()
    if not toks or toks[0] != 'VECT':
        raise ValueError('not a VECT file')
    k=1; npoly=int(toks[k]); nvert=int(toks[k+1]); ncolor=int(toks[k+2]); k+=3
    counts=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    _colors=[int(toks[k+i]) for i in range(npoly)]; k+=npoly
    if npoly!=1:
        raise ValueError('this minimal reader supports one polyline')
    n=abs(counts[0])
    vals=np.array([float(x) for x in toks[k:k+3*n]],float).reshape(n,3)
    return vals
