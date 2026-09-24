import numpy as np


def wave_numbers(N: int, L: float):
    dx=L/N
    q=2*np.pi*np.fft.fftfreq(N,d=dx)
    kx,ky,kz=np.meshgrid(q,q,q,indexing="ij")
    k2=kx*kx+ky*ky+kz*kz
    return kx,ky,kz,k2


def project_hat(vh, kx,ky,kz,k2):
    out=vh.copy()
    dot=kx*out[0]+ky*out[1]+kz*out[2]
    mask=k2>0
    out[0][mask]-=kx[mask]*dot[mask]/k2[mask]
    out[1][mask]-=ky[mask]*dot[mask]/k2[mask]
    out[2][mask]-=kz[mask]*dot[mask]/k2[mask]
    out[:,~mask]=0
    return out


def dealias_mask(N,kx,ky,kz):
    # Exact 2/3 truncation in integer-wave-number units.
    n=np.fft.fftfreq(N)*N
    nx,ny,nz=np.meshgrid(n,n,n,indexing="ij")
    cut=N//3
    return (np.abs(nx)<=cut)&(np.abs(ny)<=cut)&(np.abs(nz)<=cut)


def curl_hat(uh,kx,ky,kz):
    wh=np.empty_like(uh)
    wh[0]=1j*(ky*uh[2]-kz*uh[1])
    wh[1]=1j*(kz*uh[0]-kx*uh[2])
    wh[2]=1j*(kx*uh[1]-ky*uh[0])
    return wh


def velocity_from_vorticity(omega,L):
    N=omega.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L)
    wh=np.fft.fftn(omega,axes=(1,2,3))
    wh=project_hat(wh,kx,ky,kz,k2)
    uh=np.zeros_like(wh)
    mask=k2>0
    # u_hat = i (k x omega_hat) / |k|^2 from omega = curl u.
    uh[0][mask]=1j*(ky[mask]*wh[2][mask]-kz[mask]*wh[1][mask])/k2[mask]
    uh[1][mask]=1j*(kz[mask]*wh[0][mask]-kx[mask]*wh[2][mask])/k2[mask]
    uh[2][mask]=1j*(kx[mask]*wh[1][mask]-ky[mask]*wh[0][mask])/k2[mask]
    return project_hat(uh,kx,ky,kz,k2)


def rhs(uh,L,mask23=None):
    N=uh.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L)
    u=np.fft.ifftn(uh,axes=(1,2,3)).real
    wh=curl_hat(uh,kx,ky,kz)
    w=np.fft.ifftn(wh,axes=(1,2,3)).real
    cross=np.empty_like(u)
    cross[0]=u[1]*w[2]-u[2]*w[1]
    cross[1]=u[2]*w[0]-u[0]*w[2]
    cross[2]=u[0]*w[1]-u[1]*w[0]
    nh=np.fft.fftn(cross,axes=(1,2,3))
    nh=project_hat(nh,kx,ky,kz,k2)
    if mask23 is not None: nh*=mask23[None,...]
    return nh


def rk4_step(uh,dt,L,mask23):
    k1=rhs(uh,L,mask23)
    k2=rhs(uh+0.5*dt*k1,L,mask23)
    k3=rhs(uh+0.5*dt*k2,L,mask23)
    k4=rhs(uh+dt*k3,L,mask23)
    out=uh+(dt/6.0)*(k1+2*k2+2*k3+k4)
    out*=mask23[None,...]
    return out
