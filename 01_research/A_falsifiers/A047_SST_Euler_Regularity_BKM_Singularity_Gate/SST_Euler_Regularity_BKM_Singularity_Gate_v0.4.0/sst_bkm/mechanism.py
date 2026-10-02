from __future__ import annotations

import numpy as np
from .spectral import wave_numbers, curl_hat


def _ifft(a):
    return np.fft.ifftn(a,axes=(-3,-2,-1)).real


def cell_center_position(index,N,L):
    dx=L/N
    return np.asarray([-0.5*L+(int(i)+0.5)*dx for i in index],float)


def _fractional_index(x,N,L):
    dx=L/N
    # Grid values live at -L/2+(i+1/2)dx.
    return ((np.asarray(x,float)+0.5*L)/dx-0.5)%N


def interp_periodic(field,x,L):
    """Trilinear interpolation for arrays shaped (...,N,N,N)."""
    a=np.asarray(field)
    N=a.shape[-1]
    s=_fractional_index(x,N,L)
    i0=np.floor(s).astype(int); f=s-i0; i1=(i0+1)%N; i0%=N
    out=np.zeros(a.shape[:-3],dtype=float)
    for ax in (0,1):
        wx=(1-f[0]) if ax==0 else f[0]; ix=i0[0] if ax==0 else i1[0]
        for ay in (0,1):
            wy=(1-f[1]) if ay==0 else f[1]; iy=i0[1] if ay==0 else i1[1]
            for az in (0,1):
                wz=(1-f[2]) if az==0 else f[2]; iz=i0[2] if az==0 else i1[2]
                out += float(wx*wy*wz)*a[...,ix,iy,iz]
    return out


def wrap_position(x,L):
    return ((np.asarray(x,float)+0.5*L)%L)-0.5*L


def full_fields(uh,L,pressure_hessian=False):
    N=uh.shape[1]
    kx,ky,kz,k2=wave_numbers(N,L); ks=(kx,ky,kz)
    u=_ifft(uh)
    wh=curl_hat(uh,kx,ky,kz); w=_ifft(wh)
    G=np.empty((3,3,N,N,N),float)
    for i in range(3):
        for j in range(3):
            G[i,j]=_ifft(1j*ks[j]*uh[i])
    H=None
    if pressure_hessian:
        trG2=np.zeros((N,N,N),float)
        for i in range(3):
            for j in range(3):
                trG2 += G[i,j]*G[j,i]
        source=-trG2 # Delta p = -tr(G^2)
        sh=np.fft.fftn(source)
        ph=np.zeros_like(sh)
        mask=k2>0
        ph[mask]=-sh[mask]/k2[mask]
        H=np.empty_like(G)
        for i in range(3):
            for j in range(3):
                H[i,j]=_ifft(-ks[i]*ks[j]*ph)
    return {'u':u,'w':w,'G':G,'H':H}


def local_mechanism(G,w):
    G=np.asarray(G,float); w=np.asarray(w,float)
    S=0.5*(G+G.T)
    W=0.5*(G-G.T)
    wx,wy,wz=w
    W_expected=np.array([[0.0,-0.5*wz,0.5*wy],[0.5*wz,0.0,-0.5*wx],[-0.5*wy,0.5*wx,0.0]])
    recon=S+W_expected
    denom=max(float(np.linalg.norm(G)),1e-30)
    decomp=float(np.linalg.norm(G-recon)/denom)
    wn=float(np.linalg.norm(w))
    xi=w/wn if wn>0 else np.zeros(3)
    alpha=float(xi@S@xi) if wn>0 else 0.0
    evals=np.linalg.eigvalsh(S)
    return {
        'omega_norm':wn,'stretching_alpha':alpha,'strain_lambda_max':float(evals[-1]),
        'velocity_gradient_fro':float(np.linalg.norm(G)),
        'relative_vorticity_decomposition_error':decomp,
        'antisymmetric_tensor_error':float(np.linalg.norm(W-W_expected)/denom),
    }


class LagrangianTracker:
    """Sample-time Heun tracker for x(t) and deformation gradient F(t)."""
    def __init__(self,x0,w0):
        self.x=np.asarray(x0,float)
        self.F=np.eye(3)
        self.w0=np.asarray(w0,float)
        self.prev_fields=None
        self.prev_t=None
        self.alpha_integral=0.0
        self.prev_alpha=None
        self.samples=[]

    def sample(self,t,fields,L):
        t=float(t)
        if self.prev_fields is not None and t>self.prev_t:
            h=t-self.prev_t
            u0=interp_periodic(self.prev_fields['u'],self.x,L)
            G0=interp_periodic(self.prev_fields['G'],self.x,L)
            xpred=wrap_position(self.x+h*u0,L)
            Fpred=self.F+h*(G0@self.F)
            u1=interp_periodic(fields['u'],xpred,L)
            G1=interp_periodic(fields['G'],xpred,L)
            self.x=wrap_position(self.x+0.5*h*(u0+u1),L)
            self.F=self.F+0.5*h*((G0@self.F)+(G1@Fpred))

        w=interp_periodic(fields['w'],self.x,L)
        G=interp_periodic(fields['G'],self.x,L)
        mech=local_mechanism(G,w)
        alpha=mech['stretching_alpha']
        if self.prev_alpha is not None and self.prev_t is not None and t>self.prev_t:
            self.alpha_integral += 0.5*(self.prev_alpha+alpha)*(t-self.prev_t)
        predicted=self.F@self.w0
        cauchy=float(np.linalg.norm(w-predicted)/max(np.linalg.norm(w),np.linalg.norm(predicted),1e-30))
        deterr=float(abs(np.linalg.det(self.F)-1.0))
        logstretch=float(np.log(max(np.linalg.norm(w),1e-300)/max(np.linalg.norm(self.w0),1e-300)))
        rec={
            't':t,'x':[float(v) for v in self.x],'F':self.F.tolist(),
            'detF_minus_1_abs':deterr,'cauchy_vorticity_relative_error':cauchy,
            'alpha_integral':float(self.alpha_integral),'log_omega_ratio':logstretch,
            'alpha_logstretch_closure_abs':float(abs(self.alpha_integral-logstretch)),
            **mech,
        }
        if fields.get('H') is not None:
            H=interp_periodic(fields['H'],self.x,L)
            rec['pressure_hessian_fro']=float(np.linalg.norm(H))
            rec['_H']=H.tolist()
        self.samples.append(rec)
        self.prev_fields=fields; self.prev_t=t; self.prev_alpha=alpha
        return rec

    def finalize(self):
        rows=self.samples
        ftt=[]
        for i in range(1,len(rows)-1):
            t0,t1,t2=rows[i-1]['t'],rows[i]['t'],rows[i+1]['t']
            h1=t1-t0; h2=t2-t1
            if abs(h1-h2)>1e-9*max(h1,h2,1.0) or h1<=0: continue
            F0=np.asarray(rows[i-1]['F']); F1=np.asarray(rows[i]['F']); F2=np.asarray(rows[i+1]['F'])
            H=np.asarray(rows[i].get('_H')) if rows[i].get('_H') is not None else None
            if H is None: continue
            Fdd=(F2-2*F1+F0)/(h1*h1)
            resid=Fdd+H@F1
            ftt.append(float(np.linalg.norm(resid)/max(np.linalg.norm(Fdd),np.linalg.norm(H@F1),1e-30)))
        clean=[]
        for r in rows:
            q={k:v for k,v in r.items() if not k.startswith('_')}
            clean.append(q)
        return {
            'samples':clean,
            'summary':{
                'sample_count':len(clean),
                'max_detF_minus_1_abs':max((r['detF_minus_1_abs'] for r in clean),default=None),
                'max_cauchy_vorticity_relative_error':max((r['cauchy_vorticity_relative_error'] for r in clean),default=None),
                'max_relative_vorticity_decomposition_error':max((r['relative_vorticity_decomposition_error'] for r in clean),default=None),
                'final_alpha_logstretch_closure_abs':clean[-1]['alpha_logstretch_closure_abs'] if clean else None,
                'median_Ftt_pressure_hessian_relative_residual':float(np.median(ftt)) if ftt else None,
                'max_Ftt_pressure_hessian_relative_residual':max(ftt) if ftt else None,
            }
        }
