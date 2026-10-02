import numpy as np
from .spectral import wave_numbers,project_hat,dealias_mask,velocity_from_vorticity

try:
    from . import _native
except Exception:  # source-only validation environment; production run builds the extension first
    _native=None


def _normalize_velocity_hat(uh,L):
    N=uh.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L); mask=dealias_mask(N,kx,ky,kz)
    uh*=mask[None,...]
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    rms=np.sqrt(np.mean(np.sum(u*u,axis=0)))
    if not np.isfinite(rms) or rms<=0: raise RuntimeError("seed produced invalid/zero RMS velocity")
    return uh/rms


def _wrap(x,L):
    return x-L*np.round(x/L)


def _centerline_vorticity_seed_python(centerline,N,L,sigma,circulation_sign=1.0):
    P=np.asarray(centerline,float)
    if P.ndim!=2 or P.shape[1]!=3 or len(P)<16: raise ValueError('centerline must be (M,3), M>=16')
    tang=np.roll(P,-1,axis=0)-np.roll(P,1,axis=0)
    tang/=np.linalg.norm(tang,axis=1)[:,None]
    dx=L/N; q=-0.5*L+(np.arange(N)+0.5)*dx
    X,Y,Z=np.meshgrid(q,q,q,indexing='ij')
    out=np.zeros((3,N,N,N),float); inv=1.0/(2*sigma*sigma)
    for p,t in zip(P,tang):
        rx=_wrap(X-p[0],L); ry=_wrap(Y-p[1],L); rz=_wrap(Z-p[2],L)
        d2=rx*rx+ry*ry+rz*rz
        w=np.exp(-d2*inv)*(d2<=18*sigma*sigma)
        out[0]+=w*t[0]; out[1]+=w*t[1]; out[2]+=w*t[2]
    return circulation_sign*out


def base_trefoil(N,L,R,r,sigma,M=192):
    if _native is not None:
        omega=np.asarray(_native.trefoil_vorticity_seed(N,L,R,r,sigma,M,1.0))
    else:
        t=np.linspace(0,2*np.pi,M,endpoint=False)
        P=np.column_stack([(R+r*np.cos(3*t))*np.cos(2*t),(R+r*np.cos(3*t))*np.sin(2*t),r*np.sin(3*t)])
        omega=_centerline_vorticity_seed_python(P,N,L,sigma,1.0)
    return _normalize_velocity_hat(velocity_from_vorticity(omega,L),L)


def base_centerline(centerline,N,L,sigma):
    P=np.ascontiguousarray(np.asarray(centerline,dtype=float))
    if _native is not None:
        omega=np.asarray(_native.centerline_vorticity_seed(P,N,L,sigma,1.0))
    else:
        omega=_centerline_vorticity_seed_python(P,N,L,sigma,1.0)
    return _normalize_velocity_hat(velocity_from_vorticity(omega,L),L)


def localized_packet(uh,L,epsilon,kvec,avec,x0,sigma):
    N=uh.shape[1]; dx=L/N
    q=-0.5*L+(np.arange(N)+0.5)*dx
    X,Y,Z=np.meshgrid(q,q,q,indexing="ij")
    d=[(X-x0[0]+0.5*L)%L-0.5*L,(Y-x0[1]+0.5*L)%L-0.5*L,(Z-x0[2]+0.5*L)%L-0.5*L]
    env=np.exp(-(d[0]**2+d[1]**2+d[2]**2)/(2*sigma*sigma))
    phase=kvec[0]*d[0]+kvec[1]*d[1]+kvec[2]*d[2]
    A=np.stack([avec[c]*env*np.cos(phase) for c in range(3)],axis=0)
    Ah=np.fft.fftn(A,axes=(1,2,3)); kx,ky,kz,k2=wave_numbers(N,L)
    ph=np.empty_like(Ah)
    ph[0]=1j*(ky*Ah[2]-kz*Ah[1]); ph[1]=1j*(kz*Ah[0]-kx*Ah[2]); ph[2]=1j*(kx*Ah[1]-ky*Ah[0])
    ph=project_hat(ph,kx,ky,kz,k2); mask=dealias_mask(N,kx,ky,kz); ph*=mask[None,...]
    u=np.fft.ifftn(uh,axes=(1,2,3)).real; p=np.fft.ifftn(ph,axes=(1,2,3)).real
    ur=np.sqrt(np.mean(np.sum(u*u,axis=0))); pr=np.sqrt(np.mean(np.sum(p*p,axis=0)))
    if pr==0: return uh.copy()
    return uh + (epsilon*ur/pr)*ph
