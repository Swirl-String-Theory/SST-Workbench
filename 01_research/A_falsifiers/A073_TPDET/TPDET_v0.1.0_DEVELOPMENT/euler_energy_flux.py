"""Independent fixed-volume local energy-flux check on the EXISTING VCCR exact affine Euler flow.

This is NOT an Euler simulation of knotted finite-core vortex filaments.
The quadrature is over a stationary cube with arbitrary centre and half-side.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'references'))
from euler_qualification import velocity, pressure_over_density, euler_pde_residual


def control(t:float,center=(.2,-.1,.3),halfside=.8,n=8,h=1.e-5):
    if n<3 or h<=0 or halfside<=0:raise ValueError('invalid quadrature or geometry')
    from numpy.polynomial.legendre import leggauss
    ab,w=leggauss(n)
    ab=ab*halfside;w=w*halfside
    xyz=np.stack(np.meshgrid(ab,ab,ab,indexing='ij'),-1).reshape(-1,3)+np.array(center)
    ww=(w[:,None,None]*w[None,:,None]*w[None,None,:]).ravel()
    def volume_e(at):
        u=velocity(xyz,at)
        return float(np.sum(.5*np.einsum('ij,ij->i',u,u)*ww))
    de=(volume_e(t+h)-volume_e(t-h))/(2*h)
    flux_total=0.; faces={}
    uv=np.stack(np.meshgrid(ab,ab,indexing='ij'),-1).reshape(-1,2)
    ww2=(w[:,None]*w[None,:]).ravel()
    for axis in range(3):
        for sign in (-1,1):
            pts=np.empty((len(uv),3)); rem=[j for j in range(3) if j!=axis]
            pts[:,axis]=center[axis]+sign*halfside
            pts[:,rem]=uv+np.asarray(center)[rem]
            u=velocity(pts,t)
            p=pressure_over_density(pts,t)
            e=.5*np.einsum('ij,ij->i',u,u)
            fl=float(np.sum((e+p)*sign*u[:,axis]*ww2))
            faces['xyz'[axis]+('+' if sign>0 else '-')]=fl
            flux_total+=fl
    residual=float(de+flux_total)
    scale=max(abs(de),abs(flux_total),1e-10)
    return {'time_dimensionless':t,'volume_energy_density1':volume_e(t),
            'd_energy_dt':de,'outward_energy_flux':flux_total,
            'signed_face_fluxes':faces,'relative_energy_balance_residual':abs(residual)/scale,
            'euler_pde_residual':euler_pde_residual(t),
            'status':'PASS_EXACT_AFFINE_EULER_FLUX_CONTROL' if abs(residual)/scale<1e-7 else 'FAIL',
            'limitations':'NOT knotted finite-core Euler energy flux; no radiation/dissipation model'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='output/TPDET_v0.1.0/euler_flux_control.json');args=ap.parse_args()
    result={'model':'EXACT_AFFINE_INCOMPRESSIBLE_EULER','density_dimensionless':1,
            'region':'fixed cube, center (0.2,-0.1,0.3), half-side 0.8, Gauss-Legendre 8^3/face 8^2',
            'cases':[control(t) for t in (0.,.5,1.)]}
    result['gate']='PASS_CONTROL_ONLY' if all(x['status'].startswith('PASS') for x in result['cases']) else 'FAIL'
    dest=ROOT/args.out;dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'gate':result['gate'],'max_relative_residual':max(x['relative_energy_balance_residual'] for x in result['cases']), 'out':str(dest)}))
if __name__=='__main__':main()
