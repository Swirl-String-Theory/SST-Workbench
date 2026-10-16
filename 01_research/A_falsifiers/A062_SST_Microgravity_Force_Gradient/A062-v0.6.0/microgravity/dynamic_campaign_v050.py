"""Preregistered short-time E011 3-D pseudo-spectral Euler/NS campaign.
Dynamic simulation is in dimensionless periodic domain and is NOT a physical
microgravity or globally isolated vortex solution. Declared before FREEZE.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
from .geometry import providers
from .spectral_dynamics_v050 import test_abc_decay,integrate_e011,periodic_stress_monopole

SCHEMA='A062-V050-DYNAMIC-QUALIFICATION-1'

def _json(out,name,obj):
    out.mkdir(parents=True,exist_ok=True)
    (out/name).write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False,default=float)+'\n')

def run_dynamic(out:Path,mode:str='FULL'):
    start=time.monotonic()
    grid_sizes=[24,32] if mode=='BASIC' else [24,32,48]
    T=.012 if mode=='BASIC' else .03
    dt=.001 if mode=='BASIC' else .002
    viscosities=[0.,.005]
    p=providers(96)
    result={'schema':SCHEMA,'mode':mode,'equation':'3D incompressible velocity-form Euler/NS, Lamb(u cross curl u), projection, 2/3 de-aliased, RK4',
        'boundary':'periodic box L=1.2, zero velocity mean; NOT free-space isolated gravity',
        'time_units':'dimensionless; not SI-coupled to rc/rho_core',
        'source_initialization':'Gaussian-smoothed E011 closed centerlines; a=0.11 dimensionless; smoothing width exceeds upstream geometrical reach; only resolved coarse core',
        'source_independence':['Gilbert Fourier E011','KnotPlot VECT E011'],
        'constant_inputs':{'circulation_nondimensional':1.,'rho_f_nondimensional':1.,'kinematic_nu_screening':[0.,.005],'newton_G_input':False},
        'duration':T,'dt':dt,'grids':grid_sizes,
        'exact_reference':test_abc_decay(),
        'providers':{}, 'local_dynamic_gates':[], 'conclusions':{}}
    for name,data in p.items():
        cases={}
        for n in grid_sizes:
            for nu in viscosities:
                q=integrate_e011(data['x'],n,nu,T=T,dt=dt,L=1.2,a=.11)
                cases[f'N{n}_nu{nu:g}']=q
        result['providers'][name]={'raw_sha256':data['raw_sha256'],
            'static_geometry_only':True,'upstream_reach':data['metadata']['reach'],
            'periodic_stress_monopole':periodic_stress_monopole(data['x'],24),
            'runs':cases}
    # temporal convergence at same spatial grid (both providers), including nonzero nu
    for name,d in p.items():
        x=d['x']
        coarse=result['providers'][name]['runs']['N32_nu0.005']
        fine=integrate_e011(x,32,.005,T=T,dt=dt/2,L=1.2,a=.11)
        result['providers'][name]['dt_half_control']={'dt':fine['dt'],'last_E':fine['last']['E'],
            'relative_last_E_diff':abs(fine['last']['E']-coarse['last']['E'])/fine['last']['E'],
            'balance_error':fine['energy_balance_error']}
    errors=[];drifts=[];divs=[];proj=[]; temporal=[];spatial=[]
    for name,d in result['providers'].items():
        temporal.append(d['dt_half_control']['relative_last_E_diff'])
        for ν in viscosities:
            seq=[d['runs'][f'N{n}_nu{ν:g}']['last']['E'] for n in grid_sizes]
            spatial.append(abs(seq[-1]-seq[-2])/seq[-1])
        for run in d['runs'].values():
            divs.append(run['div_relative_max'])
            proj.append(run['initial_projection']['raw_to_projected_vorticity_rel_L2'])
            if run['nu']>0:errors.append(run['energy_balance_error'])
            else:drifts.append(abs(run['energy_relative_drift']))
    metrics={'abc_error':result['exact_reference']['relative_velocity_error'],
        'max_div_rel':max(divs),'max_euler_energy_drift':max(drifts),
        'max_NS_dissipation_budget_error':max(errors),'max_temporal_E_diff':max(temporal),
        'max_spatial_E_diff':max(spatial),'max_initial_vorticity_projection_error':max(proj)}
    thresholds={'abc_error':1e-10,'max_div_rel':1e-10,
        'max_euler_energy_drift':5e-4,
        'max_NS_dissipation_budget_error':.005,
        'max_temporal_E_diff':.002,'max_spatial_E_diff':.02,
        'max_initial_vorticity_projection_error':.03}
    passes={k:metrics[k]<thresholds[k] for k in thresholds}
    result['qualification']={'metrics':metrics,'thresholds_predeclared':thresholds,
        'pass_vector':passes,'status':'PASS' if all(passes.values()) else 'FAIL'}
    for i,(k,v) in enumerate(passes.items(),1):
        result['local_dynamic_gates'].append({'gate':f'D{i}','name':k,'status':'PASS' if v else 'FAIL',
            'value':metrics[k],'threshold':thresholds[k]})
    # Gravity source gate: nonzero E/c^2 needs constitutive coupling; in periodic
    # Poisson any k=0 source must be neutralized and cannot yield an isolated 1/r far field.
    result['conclusions']={'short_time_euler_ns_solver_qualified':bool(all(passes.values())),
        'dynamically_stable_sst_particle_claim':False,
        'clock_gravity_mechanism_derived':False,
        'periodic_stress_double_divergence_monopole_zero':True,
        'periodic_poisson_nonzero_net_mass_incompatible_without_background':True,
        'gravity_r_inverse_two_from_simulation':False,
        'nu_nonzero_is_screening_not_fundamental_SST_viscosity':True,
        'fully_resolved_core_or_topology_proved':False,
        'newton_G_derived':False}
    result['runtime_seconds']=time.monotonic()-start
    _json(out,'V050_DYNAMIC_RESULTS.json',result)
    try:
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(7.5,4.5))
        for name,d in result['providers'].items():
            for nu in viscosities:
                case=d['runs'][f'N{grid_sizes[-1]}_nu{nu:g}']
                t=[q['t'] for q in case['record']]
                E=[q['E']/case['initial']['E'] for q in case['record']]
                ax.plot(t,E,label=f'{name}: '+('Euler' if nu==0 else 'NS nu=0.005'))
        ax.set(xlabel='Time (dimensionless)',ylabel='E(t) / E(0)',title='E011 periodic vortex-tube: short-time energy evolution')
        ax.grid(alpha=.3);ax.legend(fontsize=8)
        fig.tight_layout();fig.savefig(out/'V050_DYNAMIC_ENERGY.png',dpi=160);plt.close(fig)
    except Exception as exc:
        _json(out,'V050_PLOT_WARNING.json',{'error':str(exc)})
    return result
