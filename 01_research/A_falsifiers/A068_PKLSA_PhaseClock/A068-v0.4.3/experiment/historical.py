"""Historical A/B Euler model pilot sourced externally from A004 v0.2.2.

A004 owns the XYZ data. No local historical data fallback is permitted; paths and
hashes are checked by G1 before simulation. A/B variants remain controls.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
from . import a004_adapter
from .dynamics import simulation
from .rpo import best_translation
from .floquet import tangent_fd_test
from .euler3d import Euler3D

FAMILIES=tuple(a004_adapter.FAMILIES.values())
RESOLUTIONS=a004_adapter.RESOLUTIONS
VARIANTS=('orig_ccw','orig_cw','mirrorX_ccw','mirrorX_cw')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def source_path(workbench_root,family,variant,n):
    if family not in FAMILIES or variant not in VARIANTS or n not in RESOLUTIONS:
        raise a004_adapter.A004SourceError('Unregistered A004 geometry selection')
    model={v:k for k,v in a004_adapter.FAMILIES.items()}[family]
    ch,tr=variant.rsplit('_',1)
    return a004_adapter.source_path(workbench_root,model,ch,tr,n,verify=False)

def audit(workbench_root):
    return a004_adapter.audit_library(workbench_root,check_geometry=True)

def pilot(workbench_root, mode='BASIC'):
    """Prespecified small, independently integrated Euler MODEL trajectories.

    Historical runs do not alter official v0.4.0-primary solver/gate sequence.
    Each run uses the original unchanged A064 3D Euler simulation backend.
    """
    if mode=='BASIC':
        cases=[(name,'orig_ccw',600) for name in FAMILIES];n=12;dt=.04;T=.40
    else:
        cases=[(name,tag,r) for name in FAMILIES for tag,r in (
            ('orig_ccw',600),('orig_ccw',1200),('orig_cw',600),('mirrorX_ccw',600))]
        n=12;dt=.04;T=.80
    records={}
    for name,tag,r in cases:
        path=source_path(workbench_root,name,tag,r)
        qualified_geometry_control=(mode!='BASIC' and tag=='orig_ccw' and r==600)
        summary,arrays,initial,_=simulation(path,n=n,core=.4,dt=dt,T=T,snapshots=round(T/dt)+1,
                                             track_tube=qualified_geometry_control)
        record_id=f'{name}__{tag}__N{r}'
        records[record_id]={
          'family':name,'variant':tag,'centerline_resolution':r,
          'source_sha256':sha(path),'n_3d_euler_grid':n,'model_core_width':.4,
          'time_end':T,'n_steps':summary['n_steps'],
          'max_energy_rel_drift':summary['max_energy_rel_drift'],
          'max_divergence_relative':summary['max_relative_divergence'],
          'max_cfl':summary['max_cfl'],
          'initial_enstrophy':summary['initial_enstrophy'],
          'final_enstrophy':summary['final_enstrophy'],
          'euler_conservation_screen':summary['conservation_screen_pass'],
          'relative_velocity_change':summary['end_velocity_relative_change'],
          'material_transport_and_rpo_screen_performed':qualified_geometry_control}
        if qualified_geometry_control:
            # Cheap FULL-field (all components) endpoint identity-rotation integer
            # translation control. The complete 24-rotation RPO search remains
            # exclusive to the original A068 primary; this does NOT certify RPO.
            u0=arrays['u'][0].transpose(3,0,1,2)
            uT=arrays['u'][-1].transpose(3,0,1,2)
            rpo=best_translation(u0,uT,refine=False)
            rng=np.random.default_rng(68041)
            G=Euler3D(n,.4);v=G.project(rng.normal(size=initial.shape))
            fd=tangent_fd_test(G,initial,v)
            records[record_id]['material_screen']={
                'advected_with_euler_rk4':summary['material_transport']['material_advection_performed'],
                'vortex_tube_qualified':summary['material_transport']['vortex_tube_qualified'],
                'max_volume_relative_drift':summary['material_transport']['max_relative_volume_drift'],
                'max_vorticity_tangency_mean':summary['material_transport']['max_vorticity_tangency_mean_abs_cos']}
            records[record_id]['full_field_rpo_screen']={
                'best_relative_residual':rpo['residual'],
                'screen_pass':rpo['residual']<.025,'certified_rpo':False,
                'rotations_tested':1,'translation_subgrid_refinement':False,
                'scan_period':'SHORT_EXPLORATORY_ENDPOINT_ONLY_NO_RPO_SHOOTING'}
            records[record_id]['floquet_operator_screen']={
                'tangent_linear_fd_relative_error':fd,'fd_screen_pass':fd<1e-5,
                'independent_floquet_frequency':'NOT_COMPUTED_NO_CERTIFIED_RPO'}
    n_pairs={}
    if mode!='BASIC':
        for name in FAMILIES:
            a=records[f'{name}__orig_ccw__N600']['final_enstrophy']
            b=records[f'{name}__orig_ccw__N1200']['final_enstrophy']
            n_pairs[name]={'source_point_sampling_enstrophy_difference':abs(a-b)/max(abs(b),1e-30),
                           'not_field_mesh_convergence':True,
                           'relative_to_N1200':True}
    return {'schema':'A068-HISTORICAL-EULER-PILOT-1','mode':mode,
       'source_class':'2015_NOTEBOOK_GEOMETRY_ONLY','integration_type':'ACTUAL_UNFORCED_3D_EULER_MODEL',
       'simulation_model':'DIMENSIONLESS_A064_EULER_GALERKIN',
       'no_prescribed_frequency':True,'independent_physical_providers':0,
       'test_matrix':records,'sampling_pairs':n_pairs,
       'all_model_screens_pass':all(x['euler_conservation_screen'] for x in records.values()),
       'physical_clock':'UNRESOLVED','reveal_eligibility':'NO_PHYSICAL_CLAIM',
       'limitations':'BASIC/FULL short numerical response probes; A/B N600 FULL additionally carry material transport, full-field candidate RPO and tangent-linear FD screen. Neither an RPO shooting certification nor a physical Floquet frequency/provider is established. Reflections and reversals are controls, not replicates.'}
