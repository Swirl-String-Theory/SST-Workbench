from __future__ import annotations
from pathlib import Path
import numpy as np
from .formats import load_geometry, load_vect_components, save_vect_components


def load_xyz(path):
    a=load_geometry(path)
    if len(a.components)!=1: raise ValueError('expected one component')
    return a.components[0]


def save_xyz(path, points, header='x y z'):
    np.savetxt(path,np.asarray(points,float),fmt='%.17g',header=header)


def save_vect(path, points):
    save_vect_components(path,[points])


def load_vect(path):
    c=load_vect_components(path)
    if len(c)!=1: raise ValueError('expected one VECT component')
    return c[0]
