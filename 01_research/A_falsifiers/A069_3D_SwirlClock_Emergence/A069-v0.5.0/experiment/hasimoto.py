"""A069 v0.4.0 -- genuine 1D Hasimoto/LIA time evolution, NOT 3D GP or an atomic clock.

The Hasimoto phase is globally twisted by integrated Frenet torsion. q is the
single-valued periodic gauge transform. The signed LIA coefficient reverses
under exact mirror, giving a correct parity/time-conjugacy negative control.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import numpy as np
from scipy.integrate import cumulative_trapezoid, trapezoid


def checksum(path:Path)->str:return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analytic(t:np.ndarray, kind:str, mirror:bool=False):
    t=np.asarray(t, dtype=float)
    if kind=='A':
        harmonics=[(1.0,1),(1.5,-2)]
        zamp=.35
    elif kind=='B':
        harmonics=[(2.0,2),(.5,5),(.5,-1)]
        zamp=1.0
    else:raise ValueError(kind)
    arr=[]
    for order in range(4):
        xy=sum(amp*(1j*freq)**order*np.exp(1j*freq*t) for amp,freq in harmonics)
        z=zamp*3**order*np.sin(3*t+order*np.pi/2)
        x=(-xy.real if mirror else xy.real)
        arr.append(np.stack([x,xy.imag,z],axis=-1))
    return arr


def curvature_torsion(t,kind,mirror=False):
    x,x1,x2,x3=analytic(t,kind,mirror)
    cr=np.cross(x1,x2)
    speed=np.linalg.norm(x1,axis=-1)
    crossnorm=np.linalg.norm(cr,axis=-1)
    kappa=crossnorm/speed**3
    tau=np.einsum('ij,ij->i',cr,x3)/crossnorm**2
    return kappa,tau,speed


def prepare(kind, n=256, mirror=False, fine=32768):
    if n<64 or n%2:raise ValueError('even n>=64 required')
    tf=np.linspace(0,2*np.pi,fine+1)
    _,_,v=curvature_torsion(tf,kind,mirror)
    S=cumulative_trapezoid(v,tf,initial=0.0)
    L=float(S[-1]); dst=np.arange(n)*L/n
    tn=np.interp(dst,S,tf)
    kappa,tau,_=curvature_torsion(tn,kind,mirror)
    # Geometric total torsion: high-resolution periodic integral, not a fitted phase.
    _,tautf,speedf=curvature_torsion(tf,kind,mirror)
    phasef=cumulative_trapezoid(tautf*speedf,tf,initial=0.0)
    Phi=float(phasef[-1]); delta=Phi/L
    phase=np.interp(tn,tf,phasef)
    q=kappa*np.exp(1j*(phase-delta*dst))
    x=analytic(tn,kind,mirror)[0]
    return {'kind':kind,'mirror':mirror,'n':n,'L':L,'s':dst,'t':tn,'kappa':kappa,'torsion':tau,'phi':Phi,
            'delta':delta,'q0':q,'xyz':x}


def shifted_wave_numbers(n:int,L:float,delta:float):
    return 2*np.pi*np.fft.fftfreq(n,d=L/n)+delta


def rhs(q, L, delta, beta):
    k=shifted_wave_numbers(q.size,L,delta)
    lap=np.fft.ifft(-k*k*np.fft.fft(q))
    return 1j*beta*(lap+0.5*np.abs(q)**2*q)


def strang_step(q,L,delta,beta,dt):
    k=shifted_wave_numbers(q.size,L,delta)
    out=np.fft.ifft(np.fft.fft(q)*np.exp(-.5j*beta*k*k*dt))
    out=out*np.exp(.5j*beta*np.abs(out)**2*dt)
    return np.fft.ifft(np.fft.fft(out)*np.exp(-.5j*beta*k*k*dt))


def rk4_step(q,L,delta,beta,dt):
    f=lambda x:rhs(x,L,delta,beta)
    k1=f(q);k2=f(q+dt*k1/2);k3=f(q+dt*k2/2);k4=f(q+dt*k3)
    return q+dt*(k1+2*k2+2*k3+k4)/6


def invariants(q,L,delta):
    dqs=np.fft.ifft(1j*shifted_wave_numbers(len(q),L,delta)*np.fft.fft(q))
    mass=L*np.mean(np.abs(q)**2)
    ham=L*np.mean(np.abs(dqs)**2-.25*np.abs(q)**4)
    return np.array([float(mass),float(ham)])


def integrate(q0,L,delta,beta,dt,nsteps,method):
    q=np.array(q0,dtype=complex,copy=True)
    step=strang_step if method=='strang' else rk4_step
    for _ in range(nsteps):q=step(q,L,delta,beta,dt)
    return q


def rel_err(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(a),np.linalg.norm(b),1e-30))


def audit_case(kind:str, n:int=256, steps:int=100, dt:float=3e-5):
    init=prepare(kind,n)
    mir=prepare(kind,n,True)
    q=init['q0']; qm=mir['q0']; L=init['L']; delta=init['delta']; beta=1.
    assert abs(mir['phi']+init['phi'])<1e-8
    mirror_init=rel_err(np.conj(q),qm)
    qfinal=integrate(q,L,delta,beta,dt,steps,'strang')
    qfine=integrate(q,L,delta,beta,dt/2,steps*2,'strang')
    qrk=integrate(q,L,delta,beta,dt,steps,'rk4')
    # Mirror transform is time-reversing for focusing NLS, equivalently beta -> -beta.
    qmf=integrate(qm,L,-delta,-beta,dt,steps,'strang')
    initial_inv=invariants(q,L,delta); final_inv=invariants(qfinal,L,delta)
    mass_drift=abs(final_inv[0]-initial_inv[0])/max(abs(initial_inv[0]),1e-30)
    energy_drift=abs(final_inv[1]-initial_inv[1])/max(abs(initial_inv[1]),1e-30)
    err_2step=rel_err(qfinal,qfine)
    err_rk=rel_err(qrk,qfine)
    mirror_error=rel_err(qmf,np.conj(qfinal))
    success=(mirror_init<2e-6 and mirror_error<2e-6 and mass_drift<1e-7 and
             energy_drift<5e-4 and err_2step<2e-3 and err_rk<1e-3)
    return {'kind':kind,'classification':'1D_LIA_HASIMOTO_NUMERICAL_CONTROL_ONLY','status':'PASS' if success else 'FAIL',
       'n':n,'dt':dt,'steps':steps,'total_simulation_time':dt*steps,'length':L,
       'holonomy_radians':init['phi'],'holonomy_mirror_radians':mir['phi'],
       'minimum_curvature':float(init['kappa'].min()),'maximum_curvature':float(init['kappa'].max()),
       'mass_initial':float(initial_inv[0]),'mass_final':float(final_inv[0]),
       'hamiltonian_initial':float(initial_inv[1]),'hamiltonian_final':float(final_inv[1]),
       'mass_relative_drift':float(mass_drift),'energy_relative_drift':float(energy_drift),
       'strang_time_refinement_error':err_2step,'rk4_vs_strang_refined_error':err_rk,
       'mirror_initial_error':mirror_init,'mirror_signed_flow_error':mirror_error,
       'intrinsic_3d_clock_detected':False,'physical_prediction':False,
       'qualified_3d_gp_trajectory':False,'qualified_3d_euler_trajectory':False}


def hash_audit(root):
    out={}
    for kind,name in [('A','A_Fourier_2015_p32_N1200_arclength.xyz'),('B','B_Torus_2015_p66_N1200_arclength.xyz')]:
        p=root/'sources'/'HISTORICAL_2015'/name
        dat=np.loadtxt(p)
        if dat.shape!=(1200,3):raise RuntimeError('XYZ shape invalid: '+name)
        if not np.isfinite(dat).all():raise RuntimeError('XYZ nonfinite: '+name)
        # Fail closed on source tampering and mismatched actual XYZ against analytic curve.
        pins=json.loads((root/'science_contract.json').read_text(encoding='utf-8'))['historical_source_pins']
        actual=checksum(p)
        if actual!=pins[kind]:raise ValueError('Failed frozen SHA256 pin for '+kind)
        reconstructed=prepare(kind,n=1200)['xyz']
        discrepancy=float(np.max(np.linalg.norm(dat-reconstructed,axis=1)))
        if discrepancy>1e-6:raise ValueError('XYZ and 2015 analytic parameterization disagree: '+kind)
        out[kind]={'sha256':actual,'pins_sha256':pins[kind],'source_xyz_vs_analytic_max_error':discrepancy,
                   'points':len(dat),'source':'2015-parameterization','physical_provider':False}
    return out


def suite(root,n=256,steps=100,dt=3e-5):
    cases=[audit_case(i,n,steps,dt) for i in ('A','B')]
    return {'schema':'A069-HASIMOTO-BLIND-CONTROL-1','cases':cases,
     'source_sha256':hash_audit(root),
     'status':'PASS' if all(c['status']=='PASS' for c in cases) else 'FAIL',
     'limitations':['1D LIA only','Does not establish reconstructed space-curve closure under time','No 3D GP/euler knot-field evolution','No physical clock or independent provider validation'],
     'independent_physical_provider_count':0}

if __name__=='__main__':
    r=Path(__file__).resolve().parents[1]
    print(json.dumps(suite(r),indent=2))
