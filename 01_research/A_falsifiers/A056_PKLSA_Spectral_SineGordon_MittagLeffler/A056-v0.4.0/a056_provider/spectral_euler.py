from __future__ import annotations
import numpy as np

def wave_numbers(N,L):
    q=2*np.pi*np.fft.fftfreq(N,d=L/N); return (*np.meshgrid(q,q,q,indexing="ij"),)

def _k2(ks): return ks[0]**2+ks[1]**2+ks[2]**2

def project_hat(vh,ks):
    kx,ky,kz=ks; k2=_k2(ks); out=vh.copy(); dot=kx*out[0]+ky*out[1]+kz*out[2]; m=k2>0
    out[0][m]-=kx[m]*dot[m]/k2[m]; out[1][m]-=ky[m]*dot[m]/k2[m]; out[2][m]-=kz[m]*dot[m]/k2[m]; out[:,~m]=0; return out

def dealias_mask(N):
    q=np.fft.fftfreq(N)*N; nx,ny,nz=np.meshgrid(q,q,q,indexing="ij"); cut=N//3; return (np.abs(nx)<=cut)&(np.abs(ny)<=cut)&(np.abs(nz)<=cut)

def curl_hat(uh,ks):
    kx,ky,kz=ks; wh=np.empty_like(uh); wh[0]=1j*(ky*uh[2]-kz*uh[1]); wh[1]=1j*(kz*uh[0]-kx*uh[2]); wh[2]=1j*(kx*uh[1]-ky*uh[0]); return wh

def velocity_from_vorticity(omega,L):
    N=omega.shape[1]; ks=wave_numbers(N,L); k2=_k2(ks); wh=project_hat(np.fft.fftn(omega,axes=(1,2,3)),ks); uh=np.zeros_like(wh); m=k2>0; kx,ky,kz=ks
    uh[0][m]=1j*(ky[m]*wh[2][m]-kz[m]*wh[1][m])/k2[m]; uh[1][m]=1j*(kz[m]*wh[0][m]-kx[m]*wh[2][m])/k2[m]; uh[2][m]=1j*(kx[m]*wh[1][m]-ky[m]*wh[0][m])/k2[m]
    return project_hat(uh,ks)

def rhs(uh,L,mask=None):
    N=uh.shape[1]; ks=wave_numbers(N,L); u=np.fft.ifftn(uh,axes=(1,2,3)).real; w=np.fft.ifftn(curl_hat(uh,ks),axes=(1,2,3)).real
    cross=np.cross(np.moveaxis(u,0,-1),np.moveaxis(w,0,-1)); nh=np.fft.fftn(np.moveaxis(cross,-1,0),axes=(1,2,3)); nh=project_hat(nh,ks)
    if mask is not None: nh*=mask[None,...]
    return nh

def velocity_grid(uh): return np.fft.ifftn(uh,axes=(1,2,3)).real

def interp_periodic(u,X,L):
    u=np.asarray(u,float); X=np.asarray(X,float); N=u.shape[1]; dx=L/N
    a=((X+0.5*L)/dx-0.5)%N; i0=np.floor(a).astype(int); f=a-i0; i1=(i0+1)%N; out=np.zeros_like(X)
    for bx in (0,1):
      wx=(1-f[:,0]) if bx==0 else f[:,0]; ix=i0[:,0] if bx==0 else i1[:,0]
      for by in (0,1):
        wy=(1-f[:,1]) if by==0 else f[:,1]; iy=i0[:,1] if by==0 else i1[:,1]
        for bz in (0,1):
          wz=(1-f[:,2]) if bz==0 else f[:,2]; iz=i0[:,2] if bz==0 else i1[:,2]
          wgt=wx*wy*wz
          for c in range(3): out[:,c]+=wgt*u[c,ix,iy,iz]
    return out

def rk4_coupled(uh,X,dt,L,mask):
    def stage(U,Y): return rhs(U,L,mask),interp_periodic(velocity_grid(U),Y,L)
    k1u,k1x=stage(uh,X); k2u,k2x=stage(uh+.5*dt*k1u,X+.5*dt*k1x); k3u,k3x=stage(uh+.5*dt*k2u,X+.5*dt*k2x); k4u,k4x=stage(uh+dt*k3u,X+dt*k3x)
    U=uh+(dt/6)*(k1u+2*k2u+2*k3u+k4u); U*=mask[None,...]; Y=X+(dt/6)*(k1x+2*k2x+2*k3x+k4x); Y=(Y+0.5*L)%L-0.5*L; return U,Y

def diagnostics(uh,L):
    N=uh.shape[1]; ks=wave_numbers(N,L); u=velocity_grid(uh); E=float(.5*np.mean(np.sum(u*u,axis=0))); divh=1j*(ks[0]*uh[0]+ks[1]*uh[1]+ks[2]*uh[2]); div=np.fft.ifftn(divh).real
    return {"energy":E,"div_rms":float(np.sqrt(np.mean(div*div)))}
