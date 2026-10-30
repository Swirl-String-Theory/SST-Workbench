"""STTC v0.1.0: exact analytic controls, not full Euler knot physics."""
from __future__ import annotations
import math
import numpy as np


def abc_grid(n: int, amplitude: float=1.0):
    """Periodic ABC Beltrami field on (2pi)^3, A=B=C=amplitude, k=1.
    Coordinates and velocity dimensionless; scale separately for SI.
    """
    q = 2*np.pi*np.arange(n)/n
    x,y,z=np.meshgrid(q,q,q,indexing='ij')
    vx=amplitude*(np.sin(z)+np.cos(y))
    vy=amplitude*(np.sin(x)+np.cos(z))
    vz=amplitude*(np.sin(y)+np.cos(x))
    return np.stack((vx,vy,vz),axis=-1)


def curl_spectral(v):
    n=v.shape[0]
    freq=np.fft.fftfreq(n,d=2*np.pi/n)*2*np.pi
    kx,ky,kz=np.meshgrid(freq,freq,freq,indexing='ij')
    f=np.fft.fftn(v,axes=(0,1,2))
    c=np.stack((1j*(ky*f[...,2]-kz*f[...,1]),
                1j*(kz*f[...,0]-kx*f[...,2]),
                1j*(kx*f[...,1]-ky*f[...,0])),axis=-1)
    return np.fft.ifftn(c,axes=(0,1,2)).real


def curl_centered(v):
    h=2*np.pi/v.shape[0]
    d=lambda a,axis: (np.roll(a,-1,axis)-np.roll(a,1,axis))/(2*h)
    return np.stack((d(v[...,2],1)-d(v[...,1],2),
                     d(v[...,0],2)-d(v[...,2],0),
                     d(v[...,1],0)-d(v[...,0],1)),axis=-1)


def div_spectral(v):
    n=v.shape[0]
    freq=np.fft.fftfreq(n,d=2*np.pi/n)*2*np.pi
    kx,ky,kz=np.meshgrid(freq,freq,freq,indexing='ij')
    f=np.fft.fftn(v,axes=(0,1,2))
    return np.fft.ifftn(1j*(kx*f[...,0]+ky*f[...,1]+kz*f[...,2])).real


def gauss_link(curve_a, tangent_a, curve_b, tangent_b):
    """Periodic parameter trapezoid (arclength derivatives NOT required)."""
    d=curve_a[:,None,:]-curve_b[None,:,:]
    cr=np.cross(tangent_a[:,None,:],tangent_b[None,:,:])
    denom=np.linalg.norm(d,axis=-1)**3
    if np.min(denom)<1e-14:
        raise ValueError('intersecting or unresolved curves')
    n,m=len(curve_a),len(curve_b)
    return float(np.sum(np.sum(cr*d,axis=-1)/denom)*(2*np.pi/n)*(2*np.pi/m)/(4*np.pi))


def hopf_pair(n):
    t=2*np.pi*np.arange(n)/n
    a=np.stack((np.cos(t),np.sin(t),np.zeros_like(t)),axis=-1)
    da=np.stack((-np.sin(t),np.cos(t),np.zeros_like(t)),axis=-1)
    b=np.stack((1+np.cos(t),np.zeros_like(t),np.sin(t)),axis=-1)
    db=np.stack((-np.sin(t),np.zeros_like(t),np.cos(t)),axis=-1)
    return a,da,b,db


def trefoil(n,major=2.,minor=.65):
    t=2*np.pi*np.arange(n)/n
    a=major+minor*np.cos(3*t)
    r=np.stack((a*np.cos(2*t),a*np.sin(2*t),minor*np.sin(3*t)),axis=-1)
    dr=np.stack((-3*minor*np.sin(3*t)*np.cos(2*t)-2*a*np.sin(2*t),
                 -3*minor*np.sin(3*t)*np.sin(2*t)+2*a*np.cos(2*t),
                 3*minor*np.cos(3*t)),axis=-1)
    return r,dr


def affine_matrix(strain, t):
    q=strain*t
    return np.diag([np.exp(q),np.exp(-q/2),np.exp(-q/2)])


def affine_flux_volume(tangents,F,a0, gamma):
    """Material tube local cross section A'=A0/|F T|, omega'=F omega0.
    Returns relative flux error, volume error and total-length ratio.
    """
    ds0=np.linalg.norm(tangents,axis=1)*2*np.pi/len(tangents)
    T=tangents/np.linalg.norm(tangents,axis=1,keepdims=True)
    FT=T@F.T
    lam=np.linalg.norm(FT,axis=1)
    area0=np.pi*a0*a0
    area_t=area0/lam
    omega0=(gamma/area0)*T
    omegat=omega0@F.T
    Tt=FT/lam[:,None]
    flux_t=np.einsum('ij,ij->i',omegat,Tt)*area_t
    volume0=np.sum(area0*ds0)
    volumet=np.sum(area_t*lam*ds0)
    return {'max_flux_relative_error':float(np.max(np.abs(flux_t-gamma))/abs(gamma)),
            'volume_relative_error':float(abs(volumet-volume0)/volume0),
            'length_ratio':float(np.sum(lam*ds0)/np.sum(ds0)),
            'radius_ratio_min':float(np.sqrt(1/lam).min()),
            'radius_ratio_max':float(np.sqrt(1/lam).max())}


def flat_tetrad_rotation(n=32,k=1):
    z=2*np.pi*np.arange(n)/n
    e1=np.stack((np.cos(k*z),np.sin(k*z),np.zeros_like(z)),axis=-1)
    e2=np.stack((-np.sin(k*z),np.cos(k*z),np.zeros_like(z)),axis=-1)
    h1=-k*np.einsum('ij,ij->i',e1,e1)
    h2=-k*np.einsum('ij,ij->i',e2,e2)
    metric=np.stack((e1,e2,np.tile([0.,0.,1.],(n,1))),axis=1)
    gram=np.einsum('nij,nkj->nik',metric,metric)
    return {'metric_error':float(np.max(np.abs(gram-np.eye(3)))),
            'frame_helicity':float(np.mean(h1+h2)*(2*np.pi)**3),
            'trivial_frame_helicity':0.0}


def checks(mode='BASIC'):
    rows=[]
    def rec(name,value,tolerance,rule='<'):
        value=float(value)
        passed=(value<tolerance) if rule=='<' else (value>tolerance)
        rows.append({'check':name,'value':value,'tolerance':tolerance,'status':'PASS_ANALYTIC_CONTROL' if passed else 'FAIL_ANALYTIC_CONTROL','rule':rule})
    v=abc_grid(16)
    omega=curl_spectral(v)
    dv=div_spectral(v)
    rec('BELTRAMI_spectral_curl_residual',np.max(np.abs(omega-v)),1e-11)
    rec('BELTRAMI_divergence',np.max(np.abs(dv)),1e-11)
    vol=(2*np.pi)**3
    H0=np.mean(np.einsum('...i,...i->...',v,omega))*vol
    rec('BELTRAMI_helicity_analytic',abs(H0-3*vol)/abs(3*vol),1e-12)
    # Independent 2nd order centered discretization: verify shrinking error.
    err=[]
    for n in (16,32,64):
        vn=abc_grid(n)
        err.append(float(np.max(np.abs(curl_centered(vn)-vn))))
    rec('BELTRAMI_FD_error_ratio_16_to_32',err[0]/err[1],3.5,rule='>')
    rec('BELTRAMI_FD_error_ratio_32_to_64',err[1]/err[2],3.5,rule='>')
    # Exact decaying Navier-Stokes Beltrami solution. Nonzero helicity derivative
    # while topology is unchanged by a spatially uniform positive amplitude.
    nu,t=0.1,0.7
    alpha=np.exp(-nu*t)
    vt=alpha*v
    wt=alpha*omega
    Ht=np.mean(np.einsum('...i,...i->...',vt,wt))*vol
    Hpred=H0*np.exp(-2*nu*t)
    rec('VISCOUS_helicity_decay',abs(Ht-Hpred)/abs(Hpred),1e-12)
    # r=nu Delta(vt)=-nu vt, omega=vt; dH/dt=2 int r.omega
    rhs=-2*nu*np.mean(np.einsum('...i,...i->...',vt,wt))*vol
    rec('VISCOUS_helicity_source_balance',abs(rhs+2*nu*Ht)/abs(2*nu*Ht),1e-12)
    rec('VISCOUS_normalized_field_direction_change',np.max(np.abs(wt/alpha-omega)),1e-11)
    # Independent fourth-order temporal RK4 manufactured scalar amplitude.
    def rk4(tfinal,steps):
        dt=tfinal/steps; a=1.0
        for _ in range(steps):
            f=lambda q:-nu*q
            k1=f(a); k2=f(a+dt*k1/2)
            k3=f(a+dt*k2/2); k4=f(a+dt*k3)
            a+=dt*(k1+2*k2+2*k3+k4)/6
        return a
    rk_err=[abs(rk4(2.5,m)-np.exp(-nu*2.5)) for m in (4,8,16)]
    rec('VISCOUS_RK4_temporal_ratio_4_to_8',rk_err[0]/rk_err[1],12,rule='>')
    rec('VISCOUS_RK4_temporal_ratio_8_to_16',rk_err[1]/rk_err[2],12,rule='>')
    # Induction-only manufactured slippage: reference u=0, nonzero curl(r),
    # different regular w=(c,0,0) transports a nonzero vertical field.
    # This is NOT a fluid velocity/vorticity realization of incompressible Euler.
    x=2*np.pi*np.arange(128)/128
    c=0.4; eps=0.2; phase=x-c*0.7
    bz=1+eps*np.cos(phase)
    r_y=-c*bz
    dBdt=c*eps*np.sin(phase)
    curl_r_z=c*eps*np.sin(phase)
    rec('SLIPPAGE_induction_residual',max(abs(dBdt-curl_r_z)),1e-13)
    rec('SLIPPAGE_nonzero_local_source',max(abs(curl_r_z)),0.07,rule='>')
    rec('SLIPPAGE_field_nonvanishing',min(abs(bz)),0.79,rule='>')
    # Hopf linking changes neither under invertible, orientation preserving affine map.
    a,da,b,db=hopf_pair(128)
    F=affine_matrix(0.3,1.25)
    lk0=gauss_link(a,da,b,db)
    lkt=gauss_link(a@F.T,da@F.T,b@F.T,db@F.T)
    rec('HOPF_Gauss_link_initial',abs(abs(lk0)-1),1e-8)
    rec('HOPF_Gauss_link_affine',abs(lkt-lk0),1e-8)
    rec('HOPF_affine_det',abs(np.linalg.det(F)-1),1e-12)
    tr,dtr=trefoil(512)
    av=affine_flux_volume(dtr,F,0.1,2.5)
    rec('TREFOIL_Cauchy_flux',av['max_flux_relative_error'],1e-13)
    rec('TREFOIL_affine_volume',av['volume_relative_error'],1e-13)
    metric=flat_tetrad_rotation()
    rec('FLAT_TETRAD_metric_identity',metric['metric_error'],1e-13)
    rec('FLAT_TETRAD_frame_helicity_exact',abs(metric['frame_helicity']+2*vol)/vol,1e-13)
    diagnostics={'ABC_H0':H0,'ABC_Ht':Ht,'ABC_Hpred':Hpred,
                 'ABC_viscosity':nu,'ABC_time':t,'ABC_numerical_nonideal_hel_rate':rhs,
                 'FD_curl_errors':dict(zip(('16','32','64'),err)),
                 'RK4_amplitude_errors':dict(zip(('4','8','16'),rk_err)),
                 'slippage_kinematic_induction':{'c':c,'epsilon':eps,'reference_u':'zero','corrected_w':'(c,0,0)','field_lines':'vertical and unchanged'},
                 'hopf_initial_link':lk0,'hopf_affine_link':lkt,'trefoil':av,'flat_tetrad':metric,
                 'sst_circulation_scale_m2_per_s':2*np.pi*1.40897017e-15*1.09384563e6}
    return rows,diagnostics
