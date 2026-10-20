"""Export saved material surface from existing A068 3D NPZ to independent CGAL input."""
import argparse
from pathlib import Path
import numpy as np
from .mesh_intersections import torus_triangles

def export_npz(npz,idx,out):
    with np.load(npz) as d:
        s=np.asarray(d['material_surface_unwrapped'][idx])
    v,f=torus_triangles(s)
    with open(out,'w',encoding='ascii') as h:
        h.write(f'{len(v)} {len(f)}\n')
        for xyz in v: h.write(' '.join(format(float(n),'.17g') for n in xyz)+'\n')
        for t in f: h.write(' '.join(map(str,t))+'\n')
    return {'input':str(npz),'snapshot_index':idx,'output':str(out),'vertices':len(v),'faces':len(f)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('npz');p.add_argument('--index',type=int,default=-1);p.add_argument('--output',default='material_mesh.txt')
    a=p.parse_args();print(export_npz(a.npz,a.index,a.output))
