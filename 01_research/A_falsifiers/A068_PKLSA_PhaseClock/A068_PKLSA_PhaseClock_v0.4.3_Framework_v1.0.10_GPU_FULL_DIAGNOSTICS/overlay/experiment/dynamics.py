"""A068 v0.4.3: actual dimensionless 3D Euler *simulation* from raw KnotPlot geometry.

This does not simulate experimentally validated PKLSA material tubes. No target
frequency or relativistic law is supplied. Solver code is byte-for-byte A064
Euler solver, carried forward to this test for provenance. The fields evolve.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from .euler3d import Euler3D,load_geometry,normalized_components,L
from .phaseclock import extract_shape_invariants,compare_two
from .material import create_torus,diagnostics,rk4_advect,geometry
from .rpo import full_field_rpo
from .floquet import tangent_fd_test,manufactured_floquet_test,ritz_floquet

MODEL = 'DIMENSIONLESS_GEOMETRY_SEEDED_3D_EULER_GALERKIN_NOT_PHYSICAL_PKLSA'


def stats(grid: Euler3D, U: np.ndarray, dt: float) -> dict:
    w=grid.curl(U)
    speed=np.sqrt(np.sum(U**2,axis=0))
    return {
      'E': float(.5*np.mean(np.sum(U*U,axis=0))),
      'H': float(np.mean(np.sum(U*w,axis=0))),
      'Z': float(.5*np.mean(np.sum(w*w,axis=0))),
      'divergence_relative':grid.divergence_relative(U),
      'CFL':float(dt*np.max(speed)/grid.dx),
      'rms_speed':float(np.sqrt(np.mean(speed*speed)))
    }


def simulation(source:Path,n:int=16,core:float=.4,dt:float=.04,T:float=20.,
               snapshots:int=251,retain_fields:bool=False,track_tube:bool=True):
    """No forcing/phase injection. Retain at least 128 full Euler snapshots for phase screening.

    Exact requested final T requires dt divides T. The 2/3-truncated original A064
    solver is a finite-resolution numerical model. Treat q1,q2 as same-tensor
    observables, not independent proof. qZ is based on global vortex enstrophy.
    """
    steps=round(T/dt)
    if n<8 or steps<2 or not np.isclose(steps*dt,T,rtol=1e-10,atol=1e-12):
        raise ValueError('Invalid grid or time discretization; require integer T/dt')
    components,digest=load_geometry(source)
    normalized,scale=normalized_components(components)
    G=Euler3D(n=n,core=core)
    U=G.velocity_from_curve(normalized)
    initial=U.copy()
    D=np.empty((0,3,n,n,n))
    surface,tube_settings=create_torus(components,radius=0.12,sections=32,sides=10) if track_tube else (None,None)
    material_rows=[]; material_nodes=[]
    volume0=geometry(surface)['volume_abs'] if track_tube else None
    stride=max(1,int(np.ceil(steps/max(snapshots-1,1))))
    take=np.arange(0,steps+1,stride,dtype=int)  # uniform cadence, mandatory for Hilbert phase
    keep=[]; tim=[]; scalars=[]
    for it in range(steps+1):
        if it in take:
            keep.append(U.transpose(1,2,3,0).copy())
            tim.append(it*dt)
            row=stats(G,U,dt); row['t']=float(it*dt); scalars.append(row)
            if track_tube:
                tr=diagnostics(G,U,surface,volume0);tr['t']=float(it*dt)
                material_rows.append(tr);material_nodes.append(surface.copy())
        if it < steps:
            if track_tube: U,surface=rk4_advect(G,U,surface,dt)
            else:U,D=G.rk4(U,D,dt)
    t=np.asarray(tim,dtype=float)
    fields=np.asarray(keep)
    q1,q2,shape_diag=extract_shape_invariants(fields,L)
    z=np.asarray([r['Z'] for r in scalars]); e=np.asarray([r['E'] for r in scalars])
    # A distinct flow functional (enstrophy/energy) - not an independent provider.
    qZ=L*L*z/np.maximum(e,1e-30) # dimensionless normalized enstrophy/energy
    phase=compare_two(t,q1,qZ)
    q2_phase=compare_two(t,q1,q2)
    final=U
    e0=scalars[0]['E'];h0=scalars[0]['H']
    end_l2=float(np.linalg.norm(final-initial)/max(np.linalg.norm(initial),1e-30))
    E_rel=max(abs(s['E']-e0)/max(abs(e0),1e-30) for s in scalars)
    H_rel=max(abs(s['H']-h0)/max(abs(h0),1e-12) for s in scalars)
    max_div=max(s['divergence_relative'] for s in scalars)
    max_cfl=max(s['CFL'] for s in scalars)
    control={
       'divergence':max_div<1e-9,
       'energy_drift':E_rel<1e-5,
       'helicity_drift':H_rel<1e-4,
       'cfl':max_cfl<.25,
       'nontrivial_evolution':end_l2>1e-5,
       'finite_3d_fields':bool(np.all(np.isfinite(fields)))
    }
    summary={
      'schema':'SST-A068-EULER-TRAJECTORY-1',
      'model':MODEL, 'geometry_source_sha256':digest,
      'geometry_provider':'KNOTPLOT_NATIVE_SINGLE_PROVIDER_OPT_IN_UNVALIDATED_TOPOLOGY',
      'solver_provider':'A064 Euler3D (periodic 2/3-dealiased pseudo-spectral RK4)',
      'units':'dimensionless, no SI scale',
      'n':n,'core':core,'dt':dt,'T':T,'n_steps':steps,'snapshots':len(t),
      'normalization_scale_arbitrary':scale,
      'max_relative_divergence':max_div,'max_cfl':max_cfl,
      'max_energy_rel_drift':E_rel,'max_helicity_rel_drift':H_rel,
      'initial_energy':e0,'initial_helicity':h0,
      'initial_enstrophy':scalars[0]['Z'],'final_enstrophy':scalars[-1]['Z'],
      'initial_rms_speed':scalars[0]['rms_speed'],
      'end_velocity_relative_change':end_l2,
      'conservation_control':control,
      'conservation_screen_pass':all(control.values()),
      'shape_q1_clock':phase['q1'],
      'enstrophy_clock':phase['q2'],
      'independent_functional_phase_screen':phase['G3_phase_reproducibility'],
      'same_tensor_q2_phase_screen':q2_phase['G3_phase_reproducibility'],
      'phase_screen_no_claim':'Hilbert phase does not prove material vortex, relative periodic orbit, physical clock, or relativity',
      'orbit_recursion':'FULL_FIELD_SYMMETRY_SEARCH_RUN_SEPARATELY_NO_CERTIFIED_RPO',
      'material_tube':'MATERIAL_SURFACE_ADVECTED_BUT_VORTEX_TUBE_NOT_ASSUMED',
      'physical_clock':'UNRESOLVED',
      'shape_diagnostics':shape_diag,
      'material_transport':({'mesh':tube_settings,'initial':material_rows[0], 'final':material_rows[-1],
         'max_relative_volume_drift':float(max(x['material_volume_relative_drift'] for x in material_rows)),
         'max_vorticity_tangency_mean_abs_cos':float(max(x['vorticity_tangency_mean_abs_cos'] for x in material_rows)),
         'material_advection_performed':True,'vortex_tube_qualified':bool(
            max(x['material_volume_relative_drift'] for x in material_rows)<0.05 and
            max(x['vorticity_tangency_mean_abs_cos'] for x in material_rows)<0.05 and
            max(x['vorticity_tangency_max_abs_cos'] for x in material_rows)<0.1)} if track_tube else {'status':'NOT_EXECUTED'})
    }
    arrays={'t':t,'u':fields,'domain_length':np.asarray(L),'q_shape':q1,
            'q_shape_2':q2,'q_enstrophy':qZ,'energy':e,'enstrophy':z,
            'helicity':np.asarray([s['H'] for s in scalars]),
            'divergence':np.asarray([s['divergence_relative'] for s in scalars]),
            'cfl':np.asarray([s['CFL'] for s in scalars])}
    if track_tube:
        arrays['material_surface_unwrapped']=np.asarray(material_nodes)
        arrays['material_volume']=np.asarray([s['volume_abs'] for s in material_rows])
        arrays['vorticity_tangency_mean']=np.asarray([s['vorticity_tangency_mean_abs_cos'] for s in material_rows])
    return summary,arrays,initial,final


def refinement(source:Path,mode:str='FULL',out_dir:Path|None=None):
    """Independently execute multiple Euler trajectories without target-frequency tuning.

    SIMPLE: 16^3 0..6.0, 151 snapshots. FULL/CERTIFY: 16^3 0..20,
    24^3 spatial comparison, n=16 half-dt and finite-core alternatives.
    Stored trajectories are from numerical simulation, never physical PKLSA data.
    """
    major=(mode!='BASIC')
    T=20.0 if major else 6.0
    primary_dt=.04
    base,fields,initial,final=simulation(source,16,.4,primary_dt,T,retain_fields=True,track_tube=True)
    screens={'primary':base}
    # Full-field relative symmetry candidates (all velocity degrees of freedom).
    # Need nonlinear shooting, second return, mesh/time agreement, and no drift before certification.
    rpo=full_field_rpo(fields['t'],fields['u'],minimum_period=1.5 if major else 1.,tol=.025,rotate=True,top_k=6)
    from .euler3d import Euler3D
    gfd=Euler3D(16,.4)
    rng=np.random.default_rng(6840)
    fd_probe=gfd.project(rng.normal(size=initial.shape))
    fd_error=tangent_fd_test(gfd,initial,fd_probe)
    operator={'tangent_fd_relative_error':fd_error,'tangent_fd_screen_pass':fd_error<1e-5,
              'two_mode_manufactured_oracle':manufactured_floquet_test(),
              'method':'A064 analytic tangent-linear Euler/FFT; no scalar phase input',
              'actual_euler_floquet':'NOT_EXECUTED_NO_CERTIFIED_RPO',
              'prediction_status':'UNRESOLVED'}
    # Conditional *Ritz* evaluation is an actual Euler monodromy computation,
    # never a certified Floquet frequency on an unresolved base orbit.
    if rpo['screen_pass'] and base['material_transport']['vortex_tube_qualified']:
        candidate=rpo['best']
        operator['candidate_ritz']=ritz_floquet(gfd,initial,.04,int(round(candidate['T_candidate']/.04)),
                         candidate['rotation'],candidate['shift_cells'],dimension=5)
        operator['actual_euler_floquet']='RITZ_SCREEN_NOT_CERTIFIED'
    if major:
        spatial,*_=simulation(source,24,.4,primary_dt,T,snapshots=251,track_tube=True)
        temporal,*_=simulation(source,16,.4,.02,T,snapshots=251,track_tube=True)
        core_lo,*_=simulation(source,16,.32,primary_dt,T,snapshots=251,track_tube=True)
        core_hi,*_=simulation(source,16,.48,primary_dt,T,snapshots=251,track_tube=True)
        screens.update(spatial=spatial,temporal=temporal,core_low=core_lo,core_high=core_hi)
        time_err=abs(base['final_enstrophy']-temporal['final_enstrophy'])/max(abs(temporal['final_enstrophy']),1e-30)
        space_err=abs(base['final_enstrophy']-spatial['final_enstrophy'])/max(abs(spatial['final_enstrophy']),1e-30)
        core_change=abs(core_lo['final_enstrophy']-core_hi['final_enstrophy'])/max(abs(base['final_enstrophy']),1e-30)
        checks={
          'temporal_relative_Z':time_err,
          'spatial_relative_Z':space_err,
          'finite_core_relative_spread_Z':core_change,
          'temporal_gate':time_err<.025,
          'spatial_gate':space_err<.025,
          'finite_core_robust_gate':core_change<.05,
        }
    else:
        checks={'status':'NOT_EXECUTED_IN_BASIC'}
    result={'schema':'A068-TRANCHE-v0.4.3','mode':mode,'geometry_class':'native_KnotPlot_3_1',
       'simulation_model':'GEOMETRY_INITIALIZED_PERIODIC_EULER',
       'runs':screens,'convergence':checks,'rpo':rpo,'floquet':operator,
       'scientific_qualification':{
         'geometry':'UNVERIFIED_TOPOLOGY_IDENTITY_AND_NATIVE_KNOTPLOT_RELAXATION',
         'material_core':'UNRESOLVED_AFTER_MATERIAL_ADVECTION_TANGENCY_AND_VOLUME_SCREEN',
         'frequency_prediction':'INDEPENDENT_TANGENT_OPERATOR_QUALIFIED_FD_BUT_NO_CERTIFIED_RPO_FLOQUET',
         'physical_calibration':'NO_SI_TIME_OR_CANONICAL_CORE',
         'independent_providers':'UNRESOLVED_SINGLE_KNOTPLOT_SOURCE',
         'physical_clock':'UNRESOLVED'
       }}
    if out_dir:
        out_dir.mkdir(parents=True,exist_ok=True)
        (out_dir/'EULER_DYNAMICS_RESULTS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
        (out_dir/'RPO_AND_FLOQUET_DIAGNOSTICS.json').write_text(json.dumps({'rpo':rpo,'floquet':operator},indent=2,allow_nan=False)+'\n')
        (out_dir/'MATERIAL_TUBE_DIAGNOSTICS.json').write_text(json.dumps({'source_class':'geometry_seeded_model_only','source_independence':False,'primary':base['material_transport'],'refinements':{k:v['material_transport'] for k,v in screens.items() if k!='primary'}},indent=2,allow_nan=False)+'\n')
        np.savez_compressed(out_dir/'EULER_3D_FIELDS_MODEL_ONLY.npz',**fields)
    return result
