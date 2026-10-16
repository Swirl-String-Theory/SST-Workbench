"""Velocity authority. Snapshot source is primary; filament-induced field is a model."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.interpolate import RegularGridInterpolator


def file_hash(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''):
            h.update(b)
    return h.hexdigest()


class SnapshotFlow:
    """NPZ contract: x,y,z [m], t [s], v (nt,nx,ny,nz,3) [m/s]."""
    evidence_class = 'simulation_or_measured_velocity_snapshots_UNVERIFIED'
    def __init__(self, path):
        z = np.load(path, allow_pickle=False)
        for k in ('x','y','z','t','v'):
            if k not in z: raise ValueError(f'missing snapshot field {k}')
        self.axes = tuple(np.asarray(z[k], float) for k in ('x','y','z'))
        self.times = np.asarray(z['t'],float)
        self.v = np.asarray(z['v'],float)
        if len(self.times)<1 or self.v.shape != (len(self.times),*(len(a) for a in self.axes),3):
            raise ValueError('velocity snapshots must be (nt,nx,ny,nz,3)')
        if any(len(a)<5 or not np.all(np.diff(a)>0) for a in self.axes):
            raise ValueError('monotone spatial axes with >=5 samples required')
        if not np.all(np.isfinite(self.v)) or not np.all(np.isfinite(self.times)) or (len(self.times)>1 and not np.all(np.diff(self.times)>0)):
            raise ValueError('nonfinite, nonmonotone, or inconsistent snapshots')
        self._interps = [RegularGridInterpolator(self.axes, frame[...,k], bounds_error=False,fill_value=np.nan)
                         for frame in self.v for k in range(3)]
        self.path=str(path)
        self.sha256=file_hash(path)
        self.source_metadata=None
        sidecar=Path(path).with_suffix('.source.json')
        if sidecar.exists():
            meta=json.loads(sidecar.read_text(encoding='utf8'))
            if meta.get('npz_sha256')!=self.sha256:
                raise ValueError('NPZ sidecar SHA-256 mismatch; source tampering or stale sidecar')
            if meta.get('source_type')=='geometry_derived_regularized_biot_savart_simulation':
                if 'source_type' not in z or str(z['source_type'])!=meta['source_type']:
                    raise ValueError('NPZ embedded source_type disagrees with sidecar')
                self.evidence_class=meta['source_type']
            self.source_metadata=meta

    def velocity(self, points, time=0.):
        p=np.asarray(points,float).reshape(-1,3)
        t=float(time)
        if t<self.times[0] or t>self.times[-1]:
            if len(self.times)>1: raise ValueError('time outside source snapshot interval')
        if len(self.times)==1: i=j=0; alpha=0.
        else:
            i=int(np.clip(np.searchsorted(self.times,t,side='right')-1,0,len(self.times)-2));j=i+1
            alpha=(t-self.times[i])/(self.times[j]-self.times[i])
        a=np.stack([self._interps[3*i+k](p) for k in range(3)],axis=-1)
        if j==i: return a
        b=np.stack([self._interps[3*j+k](p) for k in range(3)],axis=-1)
        return a*(1-alpha)+b*alpha

    def frame(self, axes,time):
        m=np.stack(np.meshgrid(*axes,indexing='ij'),-1)
        return self.velocity(m.reshape(-1,3),time).reshape(*m.shape)


@dataclass
class FilamentFlow:
    points: np.ndarray
    core_m: float
    gamma_m2_s: float
    moving_frame_m_s: tuple=(0.,0.,0.)
    evidence_class: str='geometry_derived_regularized_biot_savart_simulation'
    def __post_init__(self):
        p=np.asarray(self.points,float)
        if p.ndim!=2 or p.shape[1]!=3 or len(p)<16 or not np.isfinite(p).all():
            raise ValueError('requires >=16 finite 3D closed centerline points')
        if self.core_m<=0 or self.gamma_m2_s==0: raise ValueError('positive core and nonzero circulation required')
        self.start=p
        self.end=np.roll(p,-1,axis=0)
        self.mid=(self.start+self.end)/2
        self.dl=self.end-self.start
    def velocity(self,points,time=0.):
        """Midpoint-segment regularized Biot-Savart approximation, velocity in m/s."""
        q=np.asarray(points,float).reshape(-1,3)
        result=np.empty_like(q)
        for b in range(0,len(q),2048):
            r=q[b:b+2048,None,:]-self.mid[None,:,:]
            den=(np.einsum('ijk,ijk->ij',r,r)+self.core_m**2)**1.5
            result[b:b+2048]=self.gamma_m2_s/(4*np.pi)*np.sum(np.cross(self.dl[None,:,:],r)/den[:,:,None],axis=1)
        return result-np.asarray(self.moving_frame_m_s)
    def frame(self,axes,time):
        p=np.stack(np.meshgrid(*axes,indexing='ij'),-1)
        return self.velocity(p.reshape(-1,3),time).reshape(*p.shape)

class AnalyticFlow:
    """Positive/negative algorithmic controls; not PKLSA physical evidence."""
    evidence_class='synthetic_control'
    def __init__(self,kind='material', speed=.2, scale=1.):
        self.kind=kind;self.speed=speed;self.scale=scale
        self.times=np.array([0.,0.4])
    def velocity(self,points,time=0.):
        p=np.asarray(points,float).reshape(-1,3)
        x,y,z=p.T
        if self.kind=='none': return np.tile([self.speed,0.,0.],(len(p),1))
        if self.kind=='strain': return np.stack([-2*x,y,z],axis=1)
        if self.kind=='translated': x=x-self.speed*time
        g=np.exp(-(x*x+y*y+z*z)/self.scale**2)
        v=np.stack([-y*g,x*g,np.zeros_like(x)],axis=1)
        if self.kind in ('leaky','translated'): v[:,0]+=self.speed
        return v
    def frame(self,axes,time):
        p=np.stack(np.meshgrid(*axes,indexing='ij'),-1)
        return self.velocity(p.reshape(-1,3),time).reshape(*p.shape)
