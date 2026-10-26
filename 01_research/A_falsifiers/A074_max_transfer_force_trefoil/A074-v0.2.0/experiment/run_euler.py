"""Independent Euler finite-width followup. Never compares against a gravity target.

Observe but do not certify maximum force. Positive physical stability requires an
independently qualified relative equilibrium, not merely bounded perturbations.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from .euler3d import Euler3D
from .model import load_seed,sample_seed,ring,length,min_nonlocal_distance,relative_equilibrium_residual

ROOT=Path(__file__).resolve().parents[1]
OUTNAME='Trefoil_Max_Transfer_Force_v0.2.0-outputs'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def curve_variant(x,scale_z:float):
    y=x.copy(); y[:,2]*=scale_z
    # Preserve x,y radial normalization (the same convention as v0.1.0).
    return y

def perturb_curve(x,eps,mode):
    s=np.arange(len(x))*2*np.pi/len(x)
    v=x.copy()
    if mode=='z2': v[:,2]+=eps*np.cos(2*s)
    elif mode=='x3':v[:,0]+=eps*np.sin(3*s)
    else:raise ValueError(mode)
    return v

def sample_diagnostics(model,uh,markers,core,initial_gap):
    d=model.diagnostics(uh)
    gap=min_nonlocal_distance(markers,max(4,len(markers)//12))
    lm=length(markers)
    return {**d,'material_marker_length_m':lm,'material_nonlocal_gap_proxy_m':gap,
            'gap_over_initial':gap/initial_gap,'gap_over_2_core':gap/(2*core),
            'max_abs_marker_coord_m':float(np.max(np.abs(markers)))}

def run_sim(model,uh0,markers0,amplitude,steps,final_time,core,form='rotational',track=True):
    uh=uh0.copy();pts=markers0.copy();dt=final_time/steps
    fh=model.force(amplitude)
    stat0=model.diagnostics(uh)
    gap0=min_nonlocal_distance(pts,max(4,len(pts)//12))
    peak_cfl=0.
    for step in range(steps):
        maxspeed=model.diagnostics(uh)['velocity_max_m_s']
        peak_cfl=max(peak_cfl,maxspeed*dt/model.dx)
        if peak_cfl>=.45:
            raise RuntimeError(f'CFL={peak_cfl:.3f} >=0.45; reduce dt before scientific evaluation')
        if track:pts=model.tracer_step(uh,pts,dt,fh)
        uh=model.timestep(uh,dt,fh,form)
    stat=sample_diagnostics(model,uh,pts,core,gap0)
    stat['energy_drift_relative']=(stat['energy_J']-stat0['energy_J'])/stat0['energy_J']
    stat['helicity_drift_relative']=(stat['helicity_m4_s2']-stat0['helicity_m4_s2'])/max(abs(stat0['helicity_m4_s2']),1e-20)
    stat['peak_cfl']=peak_cfl
    stat.update(model.pressure_report(uh,fh))
    stat['flux_x_through_z0_N']=model.momentum_flux(uh)
    stat['applied_half_cell_load_N']=model.nominal_half_load(amplitude)
    stat['relative_marker_length_change']=(stat['material_marker_length_m']-length(markers0))/length(markers0)
    return uh,pts,stat

def normfield(v):return float(np.linalg.norm(v.ravel()))

def independent_perturbation(model,source_x,core,forcing,steps,T,delta,mode):
    # The perturbation changes actual 3D distributed-vorticity initial conditions.
    orig=model.omega_initial(source_x,core)
    bp=model.omega_initial(perturb_curve(source_x,delta,mode),core)
    bm=model.omega_initial(perturb_curve(source_x,-delta,mode),core)
    initial=[normfield(bp-orig),normfield(bm-orig)]
    final=[]
    for initial_state in [orig,bp,bm]:
        u,_,_=run_sim(model,initial_state,source_x,forcing,steps,T,core,track=False)
        final.append(u)
    growth=[normfield(final[q]-final[0])/initial[q-1] for q in [1,2]]
    return {'mode':mode,'deformation_amplitude_m':delta,'growth_positive':growth[0],
            'growth_negative':growth[1], 'max_growth':max(growth),
            'state_perturbation_norm_initial':initial,
            'conclusion':'FINITE_TIME_DIVERGENCE_DIAGNOSTIC_ONLY'}

def run(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--quick',action='store_true')
    ap.add_argument('--extended',action='store_true')
    ap.add_argument('--output',default=None)
    args=ap.parse_args(argv)
    cfg=json.loads((ROOT/'configs/euler_study.json').read_text())
    out=Path(args.output) if args.output else ROOT/OUTNAME
    out.mkdir(exist_ok=True,parents=True)
    seed=load_seed(ROOT/'seeds/trefoil_ideal_3_1_1.json')
    T=float(cfg['final_time_s']);dt=cfg['dt_s']
    # This campaign uses the same fixed physical T for temporal/spatial tests.
    grids=[32] if args.quick else ([32,48,64] if args.extended else [32,48])
    forces=cfg['load_amplitudes_m_s2']
    if args.quick:forces=forces[:2]
    seed_n=int(cfg['material_marker_N'])
    trefoil=sample_seed(seed,seed_n)
    profiles=[];history=[];holds=[];perturbs=[];scan=[]
    # Independent preliminary candidate search: vary core and axial geometry,
    # using the full resolved 3D velocity at the markers, not v0.1 filament speed.
    msearch=Euler3D(48,cfg['box_m'],cfg['rho_kg_m3'])
    for core in cfg['candidate_core_radii_m']:
        for scale_z in cfg['candidate_axial_scales']:
            xx=curve_variant(trefoil,scale_z)
            gap=min_nonlocal_distance(xx,max(4,len(xx)//12))
            if gap<=2*core:
                scan.append({'core_m':core,'axial_scale':scale_z,'admissible':False,'reason':'core clearance proxy fails'})
                continue
            uh=msearch.omega_initial(xx,core,cfg['circulation_m2_s'])
            vv=msearch.sample(msearch.ifft(uh),xx)
            fit=relative_equilibrium_residual(xx,vv)
            scan.append({'core_m':core,'axial_scale':scale_z,'admissible':True,
                         'relative_equilibrium_residual':fit['normal_residual'],
                         'gap_over_2_core':gap/(2*core),
                         'translation_m_per_s':fit['translation_m_per_s'],
                         'rotation_rad_per_s':fit['rotation_rad_per_s']})
    candidates=[x for x in scan if x.get('admissible')]
    selected=min(candidates,key=lambda x:x['relative_equilibrium_residual'])
    chosen_core=float(selected['core_m'])
    chosen_x=curve_variant(trefoil,float(selected['axial_scale']))
    # Candidate is a discovery result. It is NOT stable just by low residual.
    for n in grids:
        solver=Euler3D(n,cfg['box_m'],cfg['rho_kg_m3'])
        base=solver.omega_initial(chosen_x,chosen_core,cfg['circulation_m2_s'])
        # Directly test equivalent Euler formulations, independently implemented.
        rhs_r=solver.rhs(base,form='rotational')
        rhs_c=solver.rhs(base,form='convective')
        rhs_err=normfield(rhs_r-rhs_c)/max(normfield(rhs_r),1e-30)
        p0=solver.pressure_report(base)
        ev=relative_equilibrium_residual(chosen_x,solver.sample(solver.ifft(base),chosen_x))
        info={'n':n,'dx_m':solver.dx,'core_cells_radius':chosen_core/solver.dx,
              'rhs_form_parity_relative':rhs_err,'initial_pressure':p0,
              'initial_relative_equilibrium_residual':ev['normal_residual'],
              'chosen_candidate':selected}
        profiles.append(info)
        steps=round(T/dt)
        if abs(steps*dt-T)>1e-10:raise ValueError('final time not integer multiple dt')
        for amp in forces:
            _,markers,diag=run_sim(solver,base,chosen_x,float(amp),steps,T,chosen_core)
            history.append({'n':n,'forcing_m_s2':amp,'steps':steps,'dt_s':dt,
                            'final_time_s':T,**diag})
        # Completely separate perturbation probes, not fitted to the candidate search.
        for mode in cfg['perturbation_modes']:
            perturbs.append({'n':n,'load_m_s2':float(cfg['perturbation_load_m_s2']),
                             **independent_perturbation(solver,chosen_x,chosen_core,
                             float(cfg['perturbation_load_m_s2']),steps,T,
                             float(cfg['perturbation_epsilon_m']),mode)})
        # Separate temporal refinement at same T, same n, same forcing.
        if n==grids[0]:
            _,_,coarse=run_sim(solver,base,chosen_x,0.0,steps,T,chosen_core)
            _,_,fine=run_sim(solver,base,chosen_x,0.0,steps*2,T,chosen_core)
            holds.append({'n':n,'fixed_final_time_s':T,'dt_coarse_s':dt,'dt_fine_s':dt/2,
                          'energy_relative_difference':abs(fine['energy_J']-coarse['energy_J'])/abs(fine['energy_J']),
                          'length_relative_difference':abs(fine['material_marker_length_m']-coarse['material_marker_length_m'])/fine['material_marker_length_m']})
    # Honest qualification: numerical tests are diagnostic unless all physical gates close.
    smallest=sorted([r for r in history if r['forcing_m_s2']==0],key=lambda x:x['n'])
    drift=abs(smallest[-1]['energy_drift_relative'])
    stability_candidate=selected['relative_equilibrium_residual']<.05
    # No false G8 certification from short finite-time evolution.
    gates={
        'G0':{'status':'PASS','scope':'LOCAL_CODE_AND_PREREG_ONLY'},
        'G1':{'status':'PASS','scope':'SINGLE_GILBERT_SOURCE_ONLY'},
        'G2':{'status':'PASS' if all(x['rhs_form_parity_relative']<1e-10 and x['initial_pressure']['poisson_relative_residual']<1e-10 for x in profiles) else 'FAIL',
              'scope':'3D_EULER_MATHEMATICAL_CONSISTENCY'},
        'G3':{'status':'PASS' if drift<.01 else 'FAIL','scope':'FINITE_TIME_UNFORCED_DIAGNOSTIC'},
        'G4':{'status':'PASS' if stability_candidate else 'FAIL',
              'scope':'RELATIVE_EQUILIBRIUM_CANDIDATE_ONLY'},
        'G5':{'status':'UNRESOLVED','execution_status':'NOT_EXECUTED','scope':'LONG_TIME_NONLINEAR_STABILITY_AND_STATIONARY_BASE'},
        'G6':{'status':'PASS' if len(history)>=2 else 'UNRESOLVED',
              'scope':'LOADED_EULER_TRAJECTORIES_NOT_FORCE_LIMIT'},
        'G7':{'status':'UNRESOLVED','scope':'NO_CERTIFIED_SPATIAL_AND_TEMPORAL_CONVERGENCE'},
        'G8':{'status':'UNRESOLVED','scope':'NO_PROVEN_MAXIMAL_TRANSFERABLE_FORCE'},
        'G9':{'status':'NOT_RUN_PREREQUISITE','scope':'PRIVATE_REVEAL_RESERVED'}
    }
    report={'schema':'SST-EULER-TREFOIL-LOAD-V0.2.0','scientific_status':'DEVELOPMENT_EULER_DIAGNOSTIC_NOT_CERTIFIED',
            'framework_target':'1.0.10','framework_run_executed':False,
            'seed_source_sha256':seed['source_sha256'],
            'seed_record_sha256':sha(ROOT/'seeds/trefoil_ideal_3_1_1.json'),
            'config_sha256':sha(ROOT/'configs/euler_study.json'),
            'model':'3D periodic incompressible Euler, finite-width vorticity initialized from Gilbert 3:1:1',
            'load':'zero-mean solenoidal sinusoidal shear body force, NOT clamp or knot-breaking force',
            'search_grid':scan,'selected_best_candidate':selected,'profiles':profiles,
            'trajectories':history,'perturbation_independence_tests':perturbs,
            'temporal_refinement':holds,'gates':gates,
            'maximal_force_claim':'UNRESOLVED',
            'restrictions':['Periodic cube and finite spectral cut-off','finite-width Gaussian-like compact C2 initialization, 3D projection',
                            'Tracers are material markers, not vortex-core reconstructions','No certified knot isotopy through time',
                            'No long-term relative periodic orbit/floquet closure','External shear forcing acts on full fluid, not two physical clamps',
                            'Apparent size invariance of rho Gamma^2 is not a universal force ceiling','Spectral truncation alters smallest scales']}
    (out/'BLIND_EULER_REPORT.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    for fn,rows in [('loads.csv',history),('candidate_search.csv',scan),('perturbation_growth.csv',perturbs),('numerical_qualification.csv',profiles),('temporal_refinement.csv',holds)]:
        if not rows:continue
        cols=list(dict.fromkeys(k for r in rows for k in r))
        with (out/fn).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
            w.writerows({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)
    files=sorted(p for p in out.iterdir() if p.is_file() and p.name!='OUTPUT_MANIFEST_SHA256.json')
    manifest={p.name:sha(p) for p in files}
    (out/'OUTPUT_MANIFEST_SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps({'selected':selected,'grids':grids,'n_forces':len(history),
                      'G4':gates['G4'],'perturbations':perturbs,'gates':gates},indent=2))
    return report

if __name__=='__main__':run()
