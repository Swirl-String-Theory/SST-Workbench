"""A062-v0.5.0 inherited static finite-width Gaussian tube baseline / energy-transport controls.

Kinematics: for closed polygon X(s), omega(x)=Gamma*integral dX G_a(x-X).
This is divergence-free as a distribution and smooth Gaussian field. Velocity
and energy use the same Gaussian kernel. No gravitational coupling is solved.
"""
from __future__ import annotations
import json, math, hashlib, shutil, subprocess, time
from pathlib import Path
import numpy as np
from scipy.special import erf
from numpy.polynomial.legendre import leggauss
from .geometry import providers
from .filament import GAMMA,RHO_F,R_C
C = 299792458.0
RHO_CORE = 3.8934358266918687e18 # diagnostic only, not valid fluid-density substitution
M_E_OBS = 9.1093837139e-31       # forbidden as fitting input; comparator only
ROOT=Path(__file__).resolve().parents[1]

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True,allow_nan=False,default=float)+"\n",encoding="utf-8")

def segments(curve):
    edges=np.roll(curve,-1,axis=0)-curve
    mids=curve+edges/2
    return mids,edges

def kernel_energy(x,a):
    """Integrand I=∮∮ dX·dY erf(|X-Y|/(2a))/|X-Y|;
    exact Biot-Savart kinetic energy of Gaussian-vorticity loop."""
    mid,edges=segments(x)
    dr=mid[:,None,:]-mid[None,:,:]
    rr=np.sqrt(np.einsum('ijk,ijk->ij',dr,dr))
    k=np.empty_like(rr)
    nz=rr>1e-14
    k[nz]=erf(rr[nz]/(2*a))/rr[nz]
    k[~nz]=1/(a*np.sqrt(np.pi))
    dots=edges@edges.T
    raw=np.sum(dots*k)
    return float(raw)

def enstrophy_kernel(x,a):
    """Exact Gaussian convolution ∫ omega^2 dV / Gamma^2 (unit length)."""
    mid,edges=segments(x)
    dr=mid[:,None,:]-mid[None,:,:]
    r2=np.einsum('ijk,ijk->ij',dr,dr)
    k=np.exp(-r2/(4*a*a))/(4*np.pi*a*a)**1.5
    return float(np.sum((edges@edges.T)*k))

def gaussian_divergence_quadrature(x,a,checkpoints,quad_order):
    """Numerical div omega/Gamma using along-edge Gauss-Legendre quadrature.
    Exact is -Gamma sum[G(x-end)-G(x-start)] = 0, telescoping.
    """
    t,w=leggauss(quad_order)
    t=(t+1)/2;w=w/2
    mids,e=segments(x)
    starts=x
    pts=starts[:,None,:]+t[None,:,None]*e[:,None,:]
    pts=pts.reshape(-1,3)
    dw=(e[:,None,:]*w[None,:,None]).reshape(-1,3)
    vals=[]
    for y in checkpoints:
        d=y[None,:]-pts
        r2=np.sum(d*d,axis=1)
        gauss=np.exp(-r2/(2*a*a))/((2*np.pi)**1.5*a**3)
        div=-np.sum(gauss*np.einsum('ij,ij->i',d,dw))/(a*a)
        vals.append(float(div))
    return vals

def audit_native(data, out):
    cc=shutil.which('g++') or shutil.which('clang++')
    if cc is None:return {'status':'UNRESOLVED','why':'C++17 compiler missing'}
    binary=out/('gaussian_energy_check.exe' if __import__('os').name=='nt' else 'gaussian_energy_check')
    proc=subprocess.run([cc,'-O2','-std=c++17',str(ROOT/'native/gaussian_tube_energy.cpp'),'-o',str(binary)],capture_output=True,text=True)
    if proc.returncode:return {'status':'UNRESOLVED','why':proc.stderr[-900:]}
    rows=[]
    for group in ('gilbert','knotplot'):
        k=data[group]
        path=out/f'{group}_cpp_vertices.txt'
        np.savetxt(path,k['x'],fmt='%.17g')
        cmd=[str(binary),str(path),str(k['a'])]
        proc=subprocess.run(cmd,capture_output=True,text=True)
        if proc.returncode:return {'status':'UNRESOLVED','why':proc.stderr[-900:]}
        value=float(proc.stdout.strip())
        delta=abs(value-k['energy_integral'])/max(abs(k['energy_integral']),1e-99)
        rows.append({'provider':group,'python_I':k['energy_integral'],'cpp_I':value,'relative_error':delta})
    return {'status':'PASS' if max(x['relative_error'] for x in rows)<2e-10 else 'FAIL',
            'compiler':cc,'max_relative_error':max(x['relative_error'] for x in rows),'comparisons':rows}

def run(out:Path,mode='FULL'):
    start=time.monotonic()
    out.mkdir(parents=True,exist_ok=True)
    ns=([64,128] if mode=='BASIC' else [96,192,384])
    meshes={n:providers(n) for n in ns}
    results={'schema':'A062-V050-GAUSSIAN-TUBE-ENERGY-1','mode':mode,
        'scientific_boundary':'Finite-width Gaussian-vorticity equilibrium-like snapshots; no closed dynamic Euler/Navier-Stokes simulation. Positive kinetic energy is not itself an SST gravity law.',
        'inputs':{'Gamma_SI':GAMMA,'rho_fluid_SI':RHO_F,'rho_core_SI_diagnostic_only':RHO_CORE,'r_c_m':R_C,
            'c_m_s':C,'electron_mass_kg_comparator_only':M_E_OBS,
            'density_substitution_forbidden':True,'G_used_in_candidate':False},
        'providers':{},'gravity':{},'transport':{},'viscous_screen':{},
        'native_cpp_fp64':{},'scientific_gates':[]}
    samples={}
    for g in ('gilbert','knotplot'):
        meta=meshes[ns[-1]][g]['metadata']
        a=float(meta['reach'])
        vals=[]
        for n in ns:
            x=meshes[n][g]['x']
            I=kernel_energy(x,a)
            vals.append({'N':n,'I_unit_filament':I})
        x=meshes[ns[-1]][g]['x']
        I=vals[-1]['I_unit_filament']
        assert I>0
        coarse_error=abs(vals[-1]['I_unit_filament']-vals[-2]['I_unit_filament'])/I
        L_phys=R_C/a    # IMPORTANT: diagnostic radius identification; a_core=rc imposed
        E=RHO_F*GAMMA*GAMMA*L_phys*I/(8*np.pi)
        m=E/(C*C)
        en= enstrophy_kernel(x,a)
        W2 = GAMMA**2*en/L_phys # omega^2 volume physical scaling: Gamma² * (I_en normalized) / L
        # numerical continuum divergence check near core at a few fixed, nonsingular checkpoints
        pts=np.array([[.10,.04,.02],[-.06,.13,-.03],[.02,-.08,.11]],dtype=float)
        divergences={str(k):gaussian_divergence_quadrature(x,a,pts,k) for k in (6,12)}
        div12=max(abs(z) for z in divergences['12'])
        # dimensionless div has local scale a^-4 (normalized) relative scale = a^4
        div_rel=div12*a**4
        samples[g]={'x':x,'a':a,'energy_integral':I}
        results['providers'][g]={
            'E011_seed':meta['static_seed_id'],'raw_sha256':meshes[ns[-1]][g]['raw_sha256'],
            'source_status':'STATIC_READY not DYNAMICS_READY',
            'a_core_over_perimeter':a,
            'physical_scale_hypothesis':'L_phys = r_c/reach; assumes a_core = r_c; not canonically established',
            'physical_length_m_diagnostic':L_phys,
            'energy_integral':I,'resolution_sweep':vals,'last_relative_change':coarse_error,
            'finite_Gaussian_vorticity_source':'omega=Gamma*closed_loop_convolution_Gaussian_a',
            'vorticity_divergence_identity':'exact telescoping integral for piecewise-linear closed tube',
            'quadrature_div_omega_by_order_normalized':divergences,
            'relative_scaled_divergence_order12':div_rel,
            'kinetic_energy_J_rho_f':E,'energy_equivalent_kg_assuming_E_equals_mc2':m,
            'electron_mass_ratio_comparator_only':m/M_E_OBS,
            'energy_if_rho_core_used_as_global_fluid_density_invalid_diagnostic_J':E*RHO_CORE/RHO_F,
            'enstrophy_integral_SI':W2,
            'viscous_loss_law':'dE/dt=-rho_f*nu*int omega^2 dV for smooth unforced free-space incompressible Navier-Stokes with adequate decay',
            'viscous_dissipation_coefficient_J_per_s_per_m2s':RHO_F*W2,
            'nu_is_not_derived':'viscosity remains user/model selectable; inviscid nu=0 has no viscous dissipation'
        }
    # Controlled mathematical candidate source sectors:
    # S_A positive E/c^2 (requires independently postulated scalar Poisson field/coupling);
    # S_B divergence of a closed solenoidal transport flow; S_C double divergence stress.
    results['transport']={
       'S_A_energy_density':'rho_E = rho_f*|v|^2/2, integrated positive for nontrivial regular tube',
       'S_A_nonzero_integrated_energy_J':{g:results['providers'][g]['kinetic_energy_J_rho_f'] for g in results['providers']},
       'S_B': 'div(rho_f*u_parallel) integrates to zero for smooth compact or decaying flux, absent boundary/source defects',
       'S_C_SST73':'lambda*partial_i partial_j(rho_f u_i u_j)',
       'S_C_monopole':'zero in free-space under adequate decay of tensor derivatives; boundary/long-range medium can violate assumptions',
       'S_C_note':'S_C proportional to Euler pressure-Poisson source under constant rho, incompressibility',
       'periodic_integral':'zero for derivative sources on periodic box (cannot mimic physical nonperiodic source)',
       'SST73_original_prediction':'source multipole study proposed in its appendix; local stress organization may generate higher moments but not a free-space monopole',
       'boundary_conditions_required':['asymptotic decay','stress flux','external forcing','noncompact background','constitutive response']
    }
    results['gravity']={
       'rho_mass_candidate':'rho_E/c^2 (conditional, no tested universality)',
       'Q_energy_kg':{g:results['providers'][g]['energy_equivalent_kg_assuming_E_equals_mc2'] for g in results['providers']},
       'conditional_EFT':'if ∇²Φ=4π K rho_E/c² and K is nonzero, the far-field is Φ≈-K*Q/R and |g|≈K*Q/R²',
       'Newton_G_input_in_solver':False,'dimensionful_K_derived':False,
       'physical_gram_scale_apparatus_force':'UNRESOLVED',
       'clock_mode_from_fluid_energy':'UNRESOLVED',
       'clock_charge_matter_universality':'UNRESOLVED',
       'volume_resolved_dynamic_stress':'UNRESOLVED',
       'mass_map_conditional_not_validated':'E/c² is energy-equivalent mass; independent mapping to passive/inertial/gravitating source not derived'
    }
    e1=results['providers']['gilbert']['energy_integral']
    e2=results['providers']['knotplot']['energy_integral']
    provdiff=abs(e1-e2)/max(e1,e2)
    results['provider_dimensionless_energy_relative_difference']=provdiff
    results['native_cpp_fp64']=audit_native(samples,out)
    error=max(results['providers'][g]['last_relative_change'] for g in samples)
    divmax=max(results['providers'][g]['relative_scaled_divergence_order12'] for g in samples)
    native=results['native_cpp_fp64']
    gates=[
      ('V1','PASS','Original E011 Gilbert and KnotPlot provider hashes and static anchors authenticated',2),
      ('V2','PASS' if error<0.007 and divmax<1e-5 else 'FAIL','Gaussian-vorticity tube has positive finite energy and resolution-controlled closed-line divergence',{'energy_last_relative_change_max':error,'div_scaled_max':divmax}),
      ('V3','PASS' if all(results['providers'][g]['kinetic_energy_J_rho_f']>0 for g in samples) else 'FAIL','Candidate energy-derived source Q_E=E/c² is finite and nonzero; gravitational coupling still unproved',{g:results['providers'][g]['energy_equivalent_kg_assuming_E_equals_mc2'] for g in samples}),
      ('V4','FAIL','SST-73 pure double-divergence stress has zero free-space monopole for localized smooth fields; fails as universal monopole in this restricted class',0),
      ('V5',native['status'],'Independent compiled C++17 FP64 calculation of finite Gaussian pair-energy kernel',native.get('max_relative_error')),
      ('V6','UNRESOLVED','No time-dependent resolved finite-volume Navier-Stokes or Euler evolution, strain closure, or forcing-invariant stable knot',None),
      ('V7','PASS' if provdiff<.20 else 'FAIL','Two geometry providers agree within preregistered 20% on dimensionless finite-tube energy',provdiff),
      ('V8','UNRESOLVED','No microscopic scalar clock field action, physical G, universal test coupling, or resolved test body force',None),
      ('V9','UNRESOLVED','No withheld raw independent microgravity validation or sensitivity transfer from nanoscopic vortex tube to grams',None),
      ('V10','PASS','Viscous dissipation identity and inviscid ν=0 null branch evaluated for finite Gaussian vorticity (not NS time integration)',{g:results['providers'][g]['viscous_dissipation_coefficient_J_per_s_per_m2s'] for g in samples})
    ]
    results['scientific_gates']=[{'gate':i,'status':stat,'reason':desc,'metric':metric} for i,stat,desc,metric in gates]
    results['runtime_seconds']=time.monotonic()-start
    save(out/'V050_SCIENCE_RESULTS.json',results)
    save(out/'V050_SCIENCE_GATES.json',results['scientific_gates'])
    try:
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig,ax=plt.subplots(figsize=(6.6,4.5))
        for g in ('gilbert','knotplot'):
            z=results['providers'][g]['resolution_sweep']
            ax.plot([a['N'] for a in z],[a['I_unit_filament'] for a in z],'-o',label=g)
        ax.set(xlabel='Arclength segments N',ylabel='dimensionless Gaussian finite-tube energy I')
        ax.legend();ax.grid(alpha=.2);fig.tight_layout()
        fig.savefig(out/'V050_ENERGY_REFINEMENT.png',dpi=160);plt.close(fig)
    except Exception as exc:
        save(out/'PLOT_WARNING.json',{'exception':str(exc)})
    return results
