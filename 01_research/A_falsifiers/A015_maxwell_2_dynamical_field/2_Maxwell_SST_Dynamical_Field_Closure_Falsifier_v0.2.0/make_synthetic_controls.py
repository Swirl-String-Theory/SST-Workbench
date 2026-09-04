from __future__ import annotations
import shutil, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from sst_maxwell_falsifier.io import save_npz


def basis(khat):
    ref = np.array([1.0, 0.0, 0.0])
    if abs(np.dot(ref, khat)) > 0.85:
        ref = np.array([0.0, 1.0, 0.0])
    e1 = np.cross(khat, ref); e1 /= np.linalg.norm(e1)
    e2 = np.cross(khat, e1); e2 /= np.linalg.norm(e2)
    return e1, e2


def transverse_dataset(negative=False, seed=1):
    rng = np.random.default_rng(seed)
    c0 = 3.2
    ks = np.geomspace(0.5, 4.0, 24)
    kvec=[]; omega=[]; Avec=[]; power=[]; ek=[]; ee=[]
    for k in ks:
        v=rng.normal(size=3); v/=np.linalg.norm(v)
        e1,e2=basis(v)
        for e in [e1,e2]:
            kvec.append(k*v); omega.append(c0*k*(1+rng.normal(scale=2e-4)))
            Avec.append(e.astype(complex)); power.append(1.0)
            x=1+rng.normal(scale=0.005); ek.append(x); ee.append(1.0)
        kvec.append(k*v)
        omega.append((0.75*c0*k) if negative else 0.0)
        Avec.append(v.astype(complex)); power.append(1.0 if negative else 0.2)
        ek.append(1.0); ee.append(1.0)
    return {
        "kvec":np.asarray(kvec), "omega":np.asarray(omega), "Avec":np.asarray(Avec),
        "mode_power":np.asarray(power), "E_kin":np.asarray(ek), "E_el":np.asarray(ee)
    }, {"projector_applied":False,"gauge_reduced_input":False,"divergence_constraint_enforced":False,"unit_system":"normalized","control":"negative-longitudinal" if negative else "positive"}


def displacement_dataset(negative=False, seed=2):
    rng=np.random.default_rng(seed); n=240
    kvec=rng.normal(size=(n,3)); kvec*=rng.uniform(0.5,3.0,size=(n,1))/np.linalg.norm(kvec,axis=1)[:,None]
    omega=rng.uniform(0.7,4.0,size=n)
    xi=rng.normal(size=(n,3))+1j*rng.normal(size=(n,3))
    B=np.array([[1.2,0.1,-0.05],[0.02,0.9,0.07],[-0.03,0.04,1.05]])
    P0=xi@B
    def noise(shape,scale): return scale*(rng.normal(size=shape)+1j*rng.normal(size=shape))
    P=P0+noise(P0.shape,0.003*np.std(np.abs(P0)))
    J0=-1j*omega[:,None]*P0
    rho0=-1j*np.sum(kvec*P0,axis=1)
    J=J0+noise(J0.shape,0.004*np.std(np.abs(J0)))
    rho=rho0+noise(rho0.shape,0.004*np.std(np.abs(rho0)))
    if negative:
        J += noise(J.shape,0.18*np.std(np.abs(J0)))
    arr={"kvec":kvec,"omega":omega,"xi":xi,"P":P,"J":J,"rho_bound":rho}
    meta={"xi_independent":True,"P_independent":True,"J_independent":True,"rho_bound_independent":True,"unit_system":"normalized","control":"negative-current" if negative else "positive"}
    return arr,meta


def gravity_dataset(negative=False, seed=3):
    rng=np.random.default_rng(seed)
    d=np.geomspace(1.0,20.0,36); A=3.7; Einf=100.0
    U=(-A/d) if not negative else (A/d)
    E=Einf+U
    F=(-A/d**2) if not negative else (-A/d**2)  # negative control: force contradicts positive interaction energy
    F=F*(1+rng.normal(scale=0.003,size=len(d)))
    rscale=np.full_like(d,10.0); rmin=np.full_like(d,1.0)
    arr={"d":d,"E_total":E,"F_independent":F,"E_infinity":np.asarray([Einf]),"rho_E_min":rmin,"rho_E_scale":rscale}
    meta={"same_hamiltonian":True,"fully_relaxed":True,"force_independent":True,"unit_system":"normalized","control":"negative-energy-sign" if negative else "positive"}
    return arr,meta


def main():
    base=ROOT/"examples"
    for name in ["positive_control","negative_transverse","negative_displacement","negative_gravity"]:
        p=base/name
        if p.exists(): shutil.rmtree(p)
        p.mkdir(parents=True)
        tneg=name=="negative_transverse"; dneg=name=="negative_displacement"; gneg=name=="negative_gravity"
        for file,(arr,meta) in {
            "transverse.npz":transverse_dataset(tneg),
            "displacement.npz":displacement_dataset(dneg),
            "gravity.npz":gravity_dataset(gneg)
        }.items(): save_npz(p/file,arr,meta)
    print("Synthetic controls written to examples/")

if __name__=="__main__": main()
