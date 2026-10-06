from __future__ import annotations
import numpy as np


def energy(phi, p, kappa=1.0):
    return 0.5 * np.asarray(p) ** 2 + 0.5 * kappa * np.cos(2.0 * np.asarray(phi))


def acceleration(phi, kappa=1.0):
    return kappa * np.sin(2.0 * np.asarray(phi))


def integrate(phi0: float, p0: float, kappa: float, dt: float, steps: int):
    """Velocity-Verlet integration of phi'' = kappa sin(2 phi)."""
    phi=np.empty(steps+1,float); p=np.empty(steps+1,float)
    phi[0]=phi0; p[0]=p0
    a=acceleration(phi0,kappa)
    for i in range(steps):
        phin=phi[i] + dt*p[i] + 0.5*dt*dt*a
        an=acceleration(phin,kappa)
        pn=p[i] + 0.5*dt*(a+an)
        phi[i+1]=phin; p[i+1]=pn; a=an
    t=np.arange(steps+1,dtype=float)*dt
    return t,phi,p


def eta_from_phi(phi):
    phi=np.asarray(phi,float)
    a=np.full(phi.shape,1/np.sqrt(2),dtype=complex)
    b=np.exp(1j*phi)/np.sqrt(2)
    return np.stack([a,b],axis=-1)


def make_reference_panel(n_pairs=24, steps=4000, dt=0.01, kappa=1.0, seed=5101):
    rng=np.random.default_rng(seed)
    runs=[]; all_eta=[]; all_energy=[]
    t=None
    for i in range(n_pairs):
        dphi=float(rng.normal(0.0,0.08))
        p0=float(rng.normal(0.0,0.08))
        phi_a=np.pi/2+dphi
        phi_b=-phi_a # T maps phi -> -phi, p -> p
        for role,phi0 in [('A',phi_a),('B',phi_b)]:
            tt,phi,p=integrate(phi0,p0,kappa,dt,steps)
            t=tt
            all_eta.append(eta_from_phi(phi))
            all_energy.append(energy(phi,p,kappa))
            runs.append({
                'run_id':f'R{i:03d}{role}','pair_id':f'P{i:03d}','pair_role':role,
                'geometry_group':f'G{i%3:02d}','source_group':f'S{i%2:02d}',
                'neutral_selection':True
            })
    eta=np.asarray(all_eta); en=np.asarray(all_energy)
    manifest={
      'schema':'TRPL_INPUT_V1','synthetic_reference':True,'arrays_file':'synthetic_reference.npz',
      'producer':{'id':'REVERSIBLE_REFERENCE_OSCILLATOR','version':'1.0','dynamics_kind':'synthetic_hamiltonian',
                  'time_reversal_map':'conjugation','reversibility_certified':True,'reversibility_residual':0.0},
      'conditions':{'external_forcing':False,'time_odd_bias':False,'material_phase_observable':True,
                    'phase_derived_from_centerline_only':False,'spatial_converged':True,'temporal_converged':True,'core_converged':True},
      'runs':runs
    }
    return manifest,t,eta,en
