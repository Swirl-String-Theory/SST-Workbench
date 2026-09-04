from __future__ import annotations
from dataclasses import dataclass
import numpy as np
@dataclass
class Candidate:
    components:list
    profile_name:str
    axial_ratio:float
    core_fraction:float
    m:int
    n:int
    closure_offset:float
    radial_levels:list
    radial_n_dispersion:int
    rmax:float
    metadata:dict
    def to_npz(self,path):
        pts=np.vstack(self.components);off=[0]
        for c in self.components:off.append(off[-1]+len(c))
        np.savez_compressed(path,points=pts,offsets=np.asarray(off,np.int64),profile_name=np.array(self.profile_name),axial_ratio=self.axial_ratio,core_fraction=self.core_fraction,m=self.m,n=self.n,closure_offset=self.closure_offset,radial_levels=np.asarray(self.radial_levels,np.int64),radial_n_dispersion=self.radial_n_dispersion,rmax=self.rmax)

def load_candidate(path):
    z=np.load(path,allow_pickle=False);pts=z['points'];off=z['offsets'];comps=[pts[off[i]:off[i+1]] for i in range(len(off)-1)]
    return Candidate(comps,str(z['profile_name']),float(z['axial_ratio']),float(z['core_fraction']),int(z['m']),int(z['n']),float(z['closure_offset']),z['radial_levels'].astype(int).tolist(),int(z['radial_n_dispersion']),float(z['rmax']),{})
