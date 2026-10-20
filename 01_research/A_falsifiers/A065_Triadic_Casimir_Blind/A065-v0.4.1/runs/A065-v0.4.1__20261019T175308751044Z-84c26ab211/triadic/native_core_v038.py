"""A065 v0.3.8: periodic 3D vorticity-source assay, NOT a PKLSA Euler solver.

Builds a solenoidal Gaussian-smoothed closed filament source.  Periodic FFT
Helmholtz projection generates compatible u and pressure Poisson controls.
The initial smoothing width is an EXPLICIT synthetic input, never inferred
from geometry, and outputs are never certified as independent physical data.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path,obj):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')

def parse_xyz(path, stride=3):
    a=np.loadtxt(path,comments='#',usecols=(0,1,2),dtype=np.float64)
    if len(a)<100 or not np.isfinite(a).all():raise ValueError('INVALID_XYZ')
    if np.linalg.norm(a[0]-a[-1])<1.e-10:a=a[:-1]
    a=a[::stride].copy()
    if len(a)<24:raise ValueError('TOO_FEW_FILAMENT_NODES')
    return a

def grid_axes(n,L):return (np.arange(n,dtype=np.float64)-n//2)*(L/n)

def gaussian_vorticity(nodes,n=48,L=12.,a=.55,gamma=1.):
    """omega(x)=Gamma/(pi^3/2 a^3) int ds X'(s) exp(-|x-X(s)|^2/a^2).

    Closed-current convolution is divergence-free in continuum.  The trapezoidal
    filament midpoint rule is approximate and periodically projected for the
    diagnostic FFT field.  No time stepping / Euler pressure closure asserted.
    """
    if a<=0 or n<16 or L<=0:raise ValueError('BAD_CORE_PARAMETERS')
    ax=grid_axes(n,L)
    xx,yy,zz=np.meshgrid(ax,ax,ax,indexing='ij')
    omega=np.zeros((3,n,n,n),dtype=np.float64)
    seg=np.roll(nodes,-1,axis=0)-nodes
    mid=(nodes+np.roll(nodes,-1,axis=0))*.5
    coef=gamma/(math.pi**1.5*a**3)
    for ds,m in zip(seg,mid):
        d2=(xx-m[0])**2+(yy-m[1])**2+(zz-m[2])**2
        g=coef*np.exp(-d2/a**2)
        for j in range(3):omega[j]+=ds[j]*g
    return omega

def spectral_helmholtz(omega,L,rho=1.):
    """Periodic boundary FFT, mean-zero pressure. NOT free-space or wall closure."""
    n=omega.shape[-1]
    k=2*math.pi*np.fft.fftfreq(n,d=L/n)
    K=np.meshgrid(k,k,k,indexing='ij')
    k2=sum(v*v for v in K)
    denom=k2.copy();denom[0,0,0]=1.
    W=np.fft.fftn(omega,axes=(1,2,3))
    uhat=np.array([1j*(K[1]*W[2]-K[2]*W[1])/denom,
                   1j*(K[2]*W[0]-K[0]*W[2])/denom,
                   1j*(K[0]*W[1]-K[1]*W[0])/denom])
    uhat[:,0,0,0]=0
    U=np.fft.ifftn(uhat,axes=(1,2,3)).real
    wsolhat=np.array([1j*(K[1]*uhat[2]-K[2]*uhat[1]),
                      1j*(K[2]*uhat[0]-K[0]*uhat[2]),
                      1j*(K[0]*uhat[1]-K[1]*uhat[0])])
    Wsol=np.fft.ifftn(wsolhat,axes=(1,2,3)).real
    grad=np.empty((3,3,n,n,n))
    for i in range(3):
        for j in range(3):grad[i,j]=np.fft.ifftn(1j*K[j]*uhat[i]).real
    pressure_rhs=-rho*sum(grad[i,j]*grad[j,i] for i in range(3) for j in range(3))
    rhs_hat=np.fft.fftn(pressure_rhs)
    phat=-rhs_hat/denom
    phat[0,0,0]=0
    pressure=np.fft.ifftn(phat).real
    pressure_gradient=np.array([np.fft.ifftn(1j*K[j]*phat).real for j in range(3)])
    advective=np.array([sum(U[j]*grad[i,j] for j in range(3)) for i in range(3)])
    residual=advective+pressure_gradient/rho
    divu=np.fft.ifftn(sum(1j*K[i]*uhat[i] for i in range(3))).real
    divw=np.fft.ifftn(sum(1j*K[i]*wsolhat[i] for i in range(3))).real
    project_err=np.linalg.norm((Wsol-omega).ravel())/max(np.linalg.norm(omega.ravel()),1e-30)
    return {'omega':Wsol,'u':U,'p':pressure,'grad_p':pressure_gradient,
            'projection_relative_error':float(project_err),
            'div_u_rms':float(np.sqrt(np.mean(divu**2))),
            'div_omega_rms':float(np.sqrt(np.mean(divw**2))),
            'pressure_poisson_residual_rms':float(np.sqrt(np.mean((np.fft.ifftn(-k2*phat-rhs_hat)).real**2))),
            'steady_euler_residual_relative':float(np.linalg.norm(residual.ravel())/max(np.linalg.norm(advective.ravel()),1e-30))}

def interp(grid,xyz,L):
    """Trilinear interpolation on a regular periodic cell-centred grid."""
    n=grid.shape[-1]; x=np.asarray(xyz,float)
    scaled=(x+L/2)*(n/L)
    lo=np.floor(scaled).astype(np.int64)
    f=scaled-lo
    lo=lo%n; hi=(lo+1)%n
    out=np.zeros((grid.shape[0],len(x)),float)
    for i in (0,1):
      for j in (0,1):
       for k in (0,1):
        ids=(hi if i else lo)[:,0],(hi if j else lo)[:,1],(hi if k else lo)[:,2]
        w=(f[:,0] if i else 1-f[:,0])*(f[:,1] if j else 1-f[:,1])*(f[:,2] if k else 1-f[:,2])
        out+=grid[(slice(None),*ids)]*w[None,:]
    return out.T

def station_frame(nodes,index):
    p=nodes[index]
    tangent=np.roll(nodes,-1,axis=0)[index]-np.roll(nodes,1,axis=0)[index]
    tangent/=np.linalg.norm(tangent)
    ref=np.array([0.,0.,1.]) if abs(tangent[2])<.85 else np.array([1.,0.,0.])
    n1=np.cross(tangent,ref);n1/=np.linalg.norm(n1)
    n2=np.cross(tangent,n1)
    return p,tangent,n1,n2

def cross_sections(omega,u,gradp,nodes,L,config,rho=1.):
    rmax=config['cross_section_radius'];nr=config['n_radial'];nt=config['n_angular']
    r=(np.arange(nr)+.5)*(rmax/nr)
    theta=(np.arange(nt)+.5)*(2*np.pi/nt)
    rr,tt=np.meshgrid(r,theta,indexing='ij')
    area=rr*(rmax/nr)*(2*np.pi/nt)
    records=[]
    for frac in config['stations']:
      index=int(frac*len(nodes))%len(nodes)
      p,t,n1,n2=station_frame(nodes,index)
      er=np.cos(tt)[...,None]*n1+np.sin(tt)[...,None]*n2
      ephi=-np.sin(tt)[...,None]*n1+np.cos(tt)[...,None]*n2
      x=p+rr[...,None]*er
      wv=interp(omega,x.reshape(-1,3),L).reshape(nr,nt,3)
      uv=interp(u,x.reshape(-1,3),L).reshape(nr,nt,3)
      gp=interp(gradp,x.reshape(-1,3),L).reshape(nr,nt,3)
      axial=np.sum(wv*t,axis=-1)
      gamma=float(np.sum(axial*area))
      signed_ratio=abs(gamma)/max(float(np.sum(abs(axial)*area)),1e-30)
      Z=float(np.sum(axial**2*area))
      Ztotal=float(np.sum(np.sum(wv**2,axis=-1)*area))
      if abs(gamma)<1e-12 or Z<=1e-14: raise ValueError('INSUFFICIENT_CORE_SIGNAL')
      a_inferred=abs(gamma)/math.sqrt(2*math.pi*Z)
      epsilon_slope=a_inferred
      epsilon_half=a_inferred*math.sqrt(math.log(2.))
      idx=np.array(config['heldout_radial_indices'],int)
      rhold=r[idx]
      u_truth=np.mean(np.sum(uv*ephi,axis=-1),axis=1)[idx]
      pressure_truth=np.mean(np.sum(gp*er,axis=-1),axis=1)[idx]
      u_pred=gamma/(2*math.pi*rhold)*(1-np.exp(-(rhold/a_inferred)**2))
      dp_pred=rho*u_pred**2/rhold
      u_rms=float(np.linalg.norm(u_pred-u_truth)/max(np.linalg.norm(u_truth),1e-15))
      p_rms=float(np.linalg.norm(dp_pred-pressure_truth)/max(np.linalg.norm(pressure_truth),1e-15))
      leakage=float(math.sqrt(max(Ztotal-Z,0.)/max(Ztotal,1e-30)))
      admitted=bool(signed_ratio>=config['min_signed_flux_ratio'] and leakage<=config['max_nonaxial_leakage'] and abs(gamma)>=config['min_gamma_magnitude'])
      records.append({'fraction':frac,'index':index,'Gamma_cross_section':gamma,'Z_axial':Z,
                      'Z_full':Ztotal,'a_Gamma_Z_gaussian_assumption':a_inferred,
                      'epsilon_slope_equivalent':epsilon_slope,'epsilon_half_circulation_equivalent':epsilon_half,
                      'nonaxial_vorticity_fraction_rms':leakage,'signed_flux_ratio':signed_ratio,
                      'section_admissible':admitted,
                      'heldout_radial_points':len(idx),
                      'heldout_velocity_rms_relative':u_rms,
                      'heldout_radial_pressure_gradient_rms_relative':p_rms,
                      'model_predictive_gate':'PASS' if max(u_rms,p_rms)<config['prediction_tolerance'] else 'FAIL'})
    return records

def build_synthetic(root,config,persist=True):
    root=Path(root)
    out=[];grids=[]
    for spec in config['surrogate_sources']:
      src=root/spec['relative_geometry_path']
      if sha(src)!=spec['raw_sha256']:raise ValueError('PROTECTED_SOURCE_GEOMETRY_CHANGED')
      nodes=parse_xyz(src,stride=spec['stride'])
      omega=gaussian_vorticity(nodes,config['grid_n'],config['box_length'],spec['a_seed'],spec['gamma_seed'])
      flow=spectral_helmholtz(omega,config['box_length'],config['density'])
      sections=cross_sections(flow['omega'],flow['u'],flow['grad_p'],nodes,config['box_length'],config,config['density'])
      stem=spec['id']
      if persist:
        dst=root/'outputs'/f'CORE3D_{stem}_V038.npz'
        dst.parent.mkdir(parents=True,exist_ok=True)
        np.savez_compressed(dst,omega=flow['omega'],u=flow['u'],p=flow['p'],
                            dx=np.float64(config['box_length']/config['grid_n']),
                            L=np.float64(config['box_length']),rho=np.float64(config['density']))
        grids.append({'id':stem,'file':str(dst.relative_to(root)), 'sha256':sha(dst)})
      out.append({'id':stem,'geometry_source_sha256':sha(src),'source_class':'SYNTHETIC_SMOOTHED_FILAMENT',
                  'assumed_a_seed_NOT_INFERRED':spec['a_seed'],'assumed_gamma_seed_NOT_MEASURED':spec['gamma_seed'],
                  'field_resolution':[config['grid_n']]*3,
                  'backend':'numpy-fft-periodic-fp64',
                  'numerics':{k:v for k,v in flow.items() if not isinstance(v,np.ndarray)},
                  'cross_sections':sections})
    return out,grids

def verify_native_source(path,metadata_path):
    """Import interface; hard fail for missing provenance or invalid arrays."""
    path=Path(path);metadata_path=Path(metadata_path)
    if not path.is_file() or not metadata_path.is_file():raise ValueError('NATIVE_IMPORT_MISSING')
    m=json.loads(metadata_path.read_text('utf-8'))
    if m.get('schema')!='A065-PKLSA-VOLUMETRIC-SNAPSHOT-1' or m.get('source_sha256')!=sha(path):
        raise ValueError('NATIVE_IMPORT_MANIFEST_OR_SHA_MISMATCH')
    for x in ['provider','run_id','solver_commit','boundary_conditions','time','units','source_class','independence_group']:
        if x not in m:raise ValueError('NATIVE_IMPORT_MISSING_'+x)
    if m['source_class']!='SOURCE_NATIVE_DYNAMICAL_SNAPSHOT':raise ValueError('NATIVE_SOURCE_CLASS_NOT_PHYSICAL')
    with np.load(path,allow_pickle=False) as z:
        if 'omega' not in z:raise ValueError('NATIVE_IMPORT_NO_OMEGA')
        W=np.asarray(z['omega'],dtype=np.float64)
        if W.ndim!=4 or W.shape[0]!=3 or len(set(W.shape[1:]))!=1 or not np.isfinite(W).all():raise ValueError('NATIVE_IMPORT_INVALID_OMEGA')
        n=W.shape[1]
        if n<16:raise ValueError('NATIVE_IMPORT_TOO_COARSE')
        found_holds=all(t in z for t in ('u_heldout','p_heldout'))
    return {'provider_claim_only_not_certified':m['provider'],'source_id':m['run_id'],'grid_n':n,
            'sha256':sha(path),'heldout_fields_present':found_holds,
            'external_dynamic_provider_certification':'UNRESOLVED_UNTIL_INDEPENDENT_AUDIT',
            'physical_euler':'UNRESOLVED'}

def run(root):
    root=Path(root)
    pre=root/'preregistration'/'SOURCE_NATIVE_CORE_V038.json'
    config=json.loads(pre.read_text('utf-8'))
    if config.get('schema')!='A065-V038-PREREG-1' or config.get('version')!='v0.3.8':raise ValueError('V038_PREREG_MISMATCH')
    sources,grids=build_synthetic(root,config,True)
    finite=all(math.isfinite(s['a_Gamma_Z_gaussian_assumption']) and s['a_Gamma_Z_gaussian_assumption']>0 for x in sources for s in x['cross_sections'])
    admitted=all(any(s['section_admissible'] for s in x['cross_sections']) for x in sources)
    all_admitted=all(s['section_admissible'] for x in sources for s in x['cross_sections'])
    constraints=all(x['numerics']['div_u_rms']<config['divergence_tolerance'] and x['numerics']['pressure_poisson_residual_rms']<config['poisson_tolerance'] for x in sources)
    rejects=any(s['model_predictive_gate']=='FAIL' for x in sources for s in x['cross_sections'] if s['section_admissible'])
    result={'schema':'A065-V038-CORE-RESULT-1','release':'v0.3.8','source_class':'GEOMETRY_DERIVED_SYNTHETIC_3D_NOT_PKLSA_EULER',
            'preregistration_sha256':sha(pre),'G28':'PASS' if constraints else 'FAIL','G29':'PASS' if all_admitted else 'FAIL',
            'G30':'PASS' if finite and admitted else 'UNRESOLVED',
            'G31':'FAIL' if rejects else 'PASS',
            'G32':'UNRESOLVED_NO_AUTHENTICATED_SOURCE_NATIVE_DYNAMIC_FIELD',
            'synthetic_assay_status':'EXECUTED','physical_euler':'UNRESOLVED','physical_sst_core':'UNRESOLVED',
            'field_artifacts':grids,'sources':sources,
            'policy':'G31 result applies ONLY to geometry-derived surrogate. G32 is never PASS without independent input and provider audit. No Casimir/gravity claims.'}
    write_json(root/'outputs'/'SOURCE_NATIVE_CORE_V038_RESULT.json',result)
    return result
