from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from . import native
from .geometry import resample_closed, center
from .constants import R_C, RHO_F, GAMMA_CANON

@dataclass(frozen=True)
class PhysicalScale:
    L0_m: float
    core_dimless: float
    gamma_m2_s: float
    rho_kg_m3: float

    @property
    def time_s(self) -> float:
        return self.L0_m*self.L0_m/self.gamma_m2_s
    @property
    def velocity_m_s(self) -> float:
        return self.gamma_m2_s/self.L0_m
    @property
    def energy_J(self) -> float:
        return self.rho_kg_m3*self.gamma_m2_s*self.gamma_m2_s*self.L0_m
    @property
    def impulse_kg_m_s(self) -> float:
        return self.rho_kg_m3*self.gamma_m2_s*self.L0_m*self.L0_m


def scale_from_config(cfg: dict) -> PhysicalScale:
    s = cfg.get("physical_scale", {})
    L0 = float(s.get("length_scale_rc", 12.0))*R_C
    core = float(s.get("core_radius_rc", 1.0))*R_C/L0
    return PhysicalScale(L0, core, GAMMA_CANON, RHO_F)


def kelvin_mode_coefficient(points: np.ndarray, mode: int) -> complex:
    p = center(np.asarray(points,float))
    theta = np.unwrap(np.arctan2(p[:,1],p[:,0]))
    r = np.sqrt(p[:,0]**2+p[:,1]**2)
    dr = r-r.mean()
    z = p[:,2]-p[:,2].mean()
    signal = dr + 1j*z
    return complex(np.mean(signal*np.exp(-1j*mode*theta)))


def curvature_mode_coefficient(points: np.ndarray, mode: int) -> complex:
    k = native.curvature(points)
    k = k - np.mean(k)
    n = len(k)
    idx = np.arange(n)
    return complex(np.mean(k*np.exp(-2j*np.pi*mode*idx/n)))


def shape_descriptors(points: np.ndarray, mode: int, scale: PhysicalScale) -> dict:
    p=np.asarray(points,float)
    e_dim=native.filament_energy(p, scale.core_dimless, 1.0, 1.0)
    imp_dim=native.impulse(p, 1.0, 1.0)
    k=native.curvature(p)
    q=curvature_mode_coefficient(p, mode)
    return {
        "energy_J": float(e_dim*scale.energy_J),
        "impulse_kg_m_s": (np.asarray(imp_dim)*scale.impulse_kg_m_s).tolist(),
        "curvature_mean_dimless": float(np.mean(k)),
        "curvature_rms_dimless": float(np.sqrt(np.mean(k*k))),
        "curvature_mode_re": float(q.real),
        "curvature_mode_im": float(q.imag),
        "curvature_mode_power": float(abs(q)**2),
    }


def evolve(points: np.ndarray, cfg: dict, scale: PhysicalScale, *,
           uniform_dimless=(0.0,0.0,0.0), mode: int=2,
           record_points: bool=False) -> dict:
    sim=cfg["simulation"]
    dt=float(sim["dt_dimless"]); steps=int(sim["steps"]); stride=int(sim["sample_stride"])
    reparam_every=int(sim.get("reparam_every",0))
    p=resample_closed(np.asarray(points,float), int(sim["n_points"]))
    times=[]; kelvin=[]; curv=[]; energy=[]; impulse=[]; centroid=[]; frames=[]
    u=np.asarray(uniform_dimless,float)
    for step in range(steps+1):
        if step % stride == 0:
            times.append(step*dt)
            kelvin.append(kelvin_mode_coefficient(p,mode))
            cq=curvature_mode_coefficient(p,mode); curv.append(cq)
            e=native.filament_energy(p,scale.core_dimless,1.0,1.0)*scale.energy_J
            energy.append(e)
            impulse.append(native.impulse(p,1.0,1.0)*scale.impulse_kg_m_s)
            centroid.append(np.mean(p,axis=0))
            if record_points: frames.append(p.copy())
        if step==steps: break
        p=native.rk4_step(p,dt,scale.core_dimless,1.0,u)
        if reparam_every and (step+1)%reparam_every==0:
            p=resample_closed(p,len(p))
    out={
        "time_dimless": np.asarray(times,float),
        "time_s": np.asarray(times,float)*scale.time_s,
        "kelvin_mode": np.asarray(kelvin,complex),
        "curvature_mode": np.asarray(curv,complex),
        "energy_J": np.asarray(energy,float),
        "impulse_kg_m_s": np.asarray(impulse,float),
        "centroid_dimless": np.asarray(centroid,float),
        "final_points": p,
    }
    if record_points: out["frames"]=np.asarray(frames,float)
    return out
