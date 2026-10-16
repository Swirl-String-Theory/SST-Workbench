"""A062-v0.6.0: CONSTITUTIVE gravitational source/response tests.

This calculates a free-space *conditional* Green-function response using the
kinetic-energy density from periodic E011 Euler/NS snapshots.  Re-interpreting a
periodic-cell source as isolated is a mathematical lift, NOT a derivation of an
isolated SST solution, gravity, physical c, or G.
"""
from __future__ import annotations
import json, math, shutil, subprocess, time
from pathlib import Path
import numpy as np
from scipy.special import erf
from .geometry import providers
from .spectral_dynamics_v050 import SpectralBox

HERE=Path(__file__).resolve().parents[1]
SCHEMA='A062-V060-CONDITIONAL-GRAVITY-SOURCE-1'

def write_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False,default=float)+'\n',encoding='utf-8')

def extract_cells(box, uh):
    u=box.ifft(uh)
    # rho=c=1: dimensionless kinetic charge. The units of physical K cannot be inferred.
    energy_density=0.5*np.einsum('ijkl,ijkl->jkl',u,u)
    cell_m=energy_density*(box.length/box.n)**3
    pos=box.grid.reshape(-1,3)
    masses=cell_m.reshape(-1)
    total=float(masses.sum())
    if not (total>0 and np.isfinite(total)):
        raise ValueError('Nonpositive/nonfinite energy source')
    center=np.sum(pos*masses[:,None],axis=0)/total
    quad=np.sum(masses*np.sum((pos-center)**2,axis=1))/total
    return pos, masses, {'total_energy_charge_natural_units':total,'center_of_energy':center.tolist(), 'second_central_moment_per_Q':float(quad),
                           'source_domain':'one periodic cell L=1.2, reinterpreted as a finite isolated cell solely for conditional Green response',
                           'physical_G_supplied':False,'physical_c_supplied':False,'source_energy_density_definition':'0.5*|u|^2, dimensionless'}

def direct_field(positions,masses,query, K=1.0):
    d=query[:,None,:]-positions[None,:,:]
    rr=np.linalg.norm(d,axis=-1)
    if (rr<=0).any():raise ValueError('Probe lies on point-mass quadrature cell')
    g=-K*np.einsum('pm,pmj,m->pj',rr**-3,d,masses)
    phi=-K*np.einsum('pm,m->p',rr**-1,masses)
    return phi,g

def gaussian_reference(n=24,L=1.2,sigma=.11):
    b=SpectralBox(n,L)
    xyz=b.grid.reshape(-1,3)
    r2=np.einsum('ij,ij->i',xyz,xyz)
    densities=np.exp(-r2/(2*sigma*sigma))/(2*np.pi*sigma*sigma)**1.5
    masses=densities*(L/n)**3
    M=float(np.sum(masses))
    # exact Gaussian in infinite free space; truncation exponentially small for sigma=.11 L=1.2.
    radii=np.array([.8,1.2,2.,3.])
    queries=np.column_stack((radii,np.zeros_like(radii),np.zeros_like(radii)))
    potential,g=direct_field(xyz,masses,queries)
    z=radii/(np.sqrt(2)*sigma)
    enclosed=erf(z)-np.sqrt(2/np.pi)*(radii/sigma)*np.exp(-0.5*(radii/sigma)**2)
    analytic=enclosed/radii**2
    observed=-g[:,0]
    errors=np.abs(observed-analytic)/analytic
    return {'sigma':sigma,'grid_n':n,'mass_quadrature':M,'analytic_infinite_gaussian_mass':1.0,
            'radii':radii.tolist(),'observed_gx':g[:,0].tolist(),'analytic_magnitude':analytic.tolist(),
            'relative_errors':errors.tolist(),'max_rel_error':float(np.max(errors))}

def native_field_check(pos,mas,queries,expected,output_dir):
    compiler=shutil.which('g++') or shutil.which('clang++')
    if not compiler:return {'status':'UNRESOLVED','reason':'Native C++17 compiler not installed'}
    src=HERE/'native/gravity_green_v060.cpp'
    exe=output_dir/('gravity_green_v060.exe' if __import__('os').name=='nt' else 'gravity_green_v060')
    p=subprocess.run([compiler,'-std=c++17','-O2',str(src),'-o',str(exe)],capture_output=True,text=True)
    if p.returncode:return {'status':'UNRESOLVED','reason':p.stderr[-1300:]}
    ptsfile=output_dir/'V060_CPP_CHARGES.txt';qfile=output_dir/'V060_CPP_PROBES.txt'
    np.savetxt(ptsfile,np.column_stack((pos,mas)),fmt='%.17g')
    np.savetxt(qfile,queries,fmt='%.17g')
    p=subprocess.run([str(exe),str(ptsfile),str(qfile)],capture_output=True,text=True)
    if p.returncode:return {'status':'UNRESOLVED','reason':p.stderr[-1300:]}
    cpp=np.array([[float(x) for x in ln.split()] for ln in p.stdout.strip().splitlines()])
    delta=np.max(np.abs(cpp-expected)/np.maximum(np.abs(expected),1e-12))
    return {'status':'PASS' if delta<1e-10 else 'FAIL','max_relative_component_error':float(delta),'compiler':compiler,
            'cpp_field_shape':list(cpp.shape),'python_field_shape':list(expected.shape),'executable_sha256':__import__('hashlib').sha256(exe.read_bytes()).hexdigest()}

def gravity_snapshot(positions,masses,meta):
    center=np.array(meta['center_of_energy'])
    L=1.2
    radii=np.array([4.,6.,9.,14.,21.])*L
    vecs=np.array([[1.,0,0],[0,1.,0],[0,0,1.]])
    queries=np.array([center+direction*r for direction in vecs for r in radii])
    potential,g=direct_field(positions,masses,queries)
    magnitudes=[]; slopes=[]; errors=[]
    Q=meta['total_energy_charge_natural_units']
    for j,direction in enumerate(vecs):
        gg=np.array([-np.dot(g[j*len(radii)+k], direction) for k in range(len(radii))])
        if not np.all(gg>0):raise AssertionError('Expected attractive conditional scalar Green field')
        slope=-float(np.polyfit(np.log(radii),np.log(gg),1)[0])
        slopes.append(slope)
        errors.append(float(np.max(abs(gg*radii**2/Q-1))))
        magnitudes.append(gg.tolist())
    return {'radius_over_box':[4.,6.,9.,14.,21.], 'physical_far_field_claim':False,
            'normalized_green_coupling_K':1.0,'force_definition':'conditional g = -gradPhi; passive q/m not derived',
            'energy_source_Q':Q,'axes':['x','y','z'],'conditional_radial_g_magnitudes':magnitudes,
            'exponents':slopes,'maximum_far_field_exponent_abs_error':float(np.max(np.abs(np.array(slopes)-2))),
            'max_relative_deviation_from_monopole_at_test_radii':max(errors),
            'potential_first_query':float(potential[0]),'native_comparison_queries':queries,
            'native_comparison_python':np.column_stack((potential,g))}

def run_gravity(out:Path, mode:str='CERTIFY'):
    t0=time.monotonic(); out.mkdir(parents=True,exist_ok=True)
    ref=json.loads((HERE/'inputs/v050_windows_baseline_dynamic.json').read_text())
    p=providers(96); box=SpectralBox(24,1.2)
    T=.03 if mode!='BASIC' else .012
    dt=.002 if mode!='BASIC' else .001
    steps=int(round(T/dt))
    results={'schema':SCHEMA,'mode':mode,'hypotheses':{'H_E':'E/c^2 hydrodynamic source positive; active charge NOT proved',
          'H_P':'free-space scalar Poisson kernel assumed; K normalized to 1; no SI Newton-G inserted',
          'H_T':'local clock algebraic mapping alone no nonlocal massless mediator',
          'H_S':'localized/periodic stress double-divergence zero monopole'},
          'bounds':{'periodic_initial_condition':True,'isolated_free_space_dynamics':False,'physical_G_derived':False,
                   'passive_body_mass_equal_charge_derived':False,'long_lived_knot':False,
                   'clock_scalar_propagation_derived':False,'full_gravity_closure':False},
          'time_basis':'same dimensionless Euler/NS solver as v0.5.0, snapshots regenerated',
          'external_baseline_label':'User Windows 20261013T182227899537Z-b96fbc73 (read only)',
          'manufactured_gaussian':gaussian_reference(), 'providers':{}, 'native_cpp_fp64':{}, 'gates':[]}
    for name,d in p.items():
        records={}
        for nu in (0.0,.005):
            uh,init=box.initial_tube(d['x'],.11)
            snapshots={}
            for k in range(steps+1):
                if k in (0,steps):
                    pos,masses,meta=extract_cells(box,uh)
                    field=gravity_snapshot(pos,masses,meta)
                    source_energy=box.diagnostics(uh)['E']
                    source_rel=abs(meta['total_energy_charge_natural_units']-source_energy)/source_energy
                    ref_key=f'N24_nu{nu:g}'
                    if T==.03:
                        rr=ref['providers'][name]['runs'][ref_key]['initial' if k==0 else 'last']['E']
                        ref_err=abs(rr-source_energy)/rr
                    else:ref_err=None
                    if k==steps:
                        qry=field.pop('native_comparison_queries'); exp=field.pop('native_comparison_python')
                        native=native_field_check(pos,masses,qry,exp,out)
                        results['native_cpp_fp64'][f'{name}_nu{nu:g}']=native
                    else:
                        field.pop('native_comparison_queries');field.pop('native_comparison_python')
                    snapshots['t0' if k==0 else 'final']={'t':k*dt,'energy_from_spectral':source_energy,
                        'source_energy_consistency_relative_error':source_rel,
                        'windows_v050_baseline_energy_relative_error':ref_err,
                        'meta':meta,'conditional_free_space_field':field}
                if k<steps:uh=box.step(uh,dt,nu)
            records[f'nu{nu:g}']=snapshots
        results['providers'][name]={'raw_sha256':d['raw_sha256'],'static_ready_not_dynamic_ready':True,
                                    'resolution_screen_note':'N24 and width a=.11, not slender; evolved snapshots of SHORT-time projected field',
                                    'snapshots':records}
    exps=[];monos=[];compare=[];src=[]; cpp=[]
    for d in results['providers'].values():
        for snap in d['snapshots'].values():
            for sm in snap.values():
                f=sm['conditional_free_space_field']
                exps.append(f['maximum_far_field_exponent_abs_error'])
                monos.append(f['max_relative_deviation_from_monopole_at_test_radii'])
                compare.append(sm['windows_v050_baseline_energy_relative_error'] if sm['windows_v050_baseline_energy_relative_error'] is not None else 0)
                src.append(sm['source_energy_consistency_relative_error'])
    for v in results['native_cpp_fp64'].values():
        if v['status']=='PASS':cpp.append(v['max_relative_component_error'])
    metrics={'max_exponent_abs_error':max(exps),'max_far_field_rel_monopole_deviation':max(monos),
             'max_energy_density_vs_spectral_error':max(src), 'max_windows_v050_energy_diff':max(compare),
             'gaussian_reference_max_rel_error':results['manufactured_gaussian']['max_rel_error'],
             'max_cpp_parity_rel_error':max(cpp) if cpp else None}
    thresholds={'max_exponent_abs_error':.03,'max_far_field_rel_monopole_deviation':.025,
      'max_energy_density_vs_spectral_error':1e-12,'max_windows_v050_energy_diff':1e-9,
      'gaussian_reference_max_rel_error':.002,'max_cpp_parity_rel_error':1e-10}
    checks={k:(metrics[k]<v if metrics[k] is not None else False) for k,v in thresholds.items()}
    results['qualification']={'metrics':metrics,'thresholds_predeclared':thresholds,'checks':checks}
    def gate(k,status,reason,metric=None):results['gates'].append({'gate':k,'status':status,'reason':reason,'metric':metric})
    gate('V12','PASS' if checks['gaussian_reference_max_rel_error'] else 'FAIL','Free-space Green gravity kernel matches independent analytic 3D Gaussian manufactured test',metrics['gaussian_reference_max_rel_error'])
    gate('V13','PASS' if all(checks[k] for k in ('max_exponent_abs_error','max_far_field_rel_monopole_deviation','max_energy_density_vs_spectral_error','max_windows_v050_energy_diff')) else 'FAIL',
         'CONDITIONAL assumed Poisson Green-field from v0.5 regenerated E011 energy; not a derived physical force',metrics)
    gate('V14','FAIL','An instantaneous purely local algebraic Swirl-Clock S(u) is spatially constant outside a compact support; provides no 1/R mediator by itself',None)
    gate('V15','UNRESOLVED','Passive gravitational charge-to-inertial mass equality has not been obtained from vortex/test-body dynamics',None)
    gate('V16','UNRESOLVED','No physical SI K=G, scalar-action stiffness, propagating clock field, or mass-map from medium first principles',None)
    gate('V17','PASS','For periodic fields the SST-73 derivative source has identically zero k=0; periodic Poisson for positive mean source needs neutrality/boundary change',0.)
    gate('V18','UNRESOLVED','No isolated slender vortex time evolution and no withheld gram-scale force-gradient raw test-body data',None)
    results['runtime_seconds']=time.monotonic()-t0
    write_json(out/'V060_GRAVITY_RESULTS.json',results)
    write_json(out/'V060_GRAVITY_GATES.json',results['gates'])
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(7.8,4.7))
        radii=np.array([4.,6.,9.,14.,21.])
        for name,d in results['providers'].items():
            f=d['snapshots']['nu0']['final']['conditional_free_space_field']
            ax.loglog(radii, f['conditional_radial_g_magnitudes'][0], 'o-',label=name+' conditional Euler')
        y0=results['providers']['gilbert']['snapshots']['nu0']['final']['conditional_free_space_field']['energy_source_Q']
        ax.loglog(radii,y0/(radii*1.2)**2,'--',label='assumed Green monopole KQ/R^2')
        ax.set(xlabel='R/L, beyond one lifted periodic cell',ylabel='|g| (dimensionless; K=1)',
               title='Conditional Poisson response: slope ≈ −2 is built into mediator')
        ax.grid(True,which='both',alpha=.22);ax.legend(fontsize=8);fig.tight_layout()
        fig.savefig(out/'V060_CONDITIONAL_FARFIELD.png',dpi=160);plt.close(fig)
    except Exception as exc:write_json(out/'V060_PLOT_WARNING.json',{'error':str(exc)})
    return results
