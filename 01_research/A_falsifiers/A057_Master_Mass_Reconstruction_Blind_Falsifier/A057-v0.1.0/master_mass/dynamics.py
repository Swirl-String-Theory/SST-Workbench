from __future__ import annotations
import numpy as np
from .geometry import as_closed,bishop_frame
from .energy import energy_matrix,total_kernel

def perturbation_basis(components,modes=2):
    comps=[as_closed(c) for c in components]; basis=[]
    offsets=np.cumsum([0]+[len(c) for c in comps]); total=offsets[-1]
    for ci,c in enumerate(comps):
        _,n,b,_=bishop_frame(c); N=len(c); theta=2*np.pi*np.arange(N)/N
        for k in range(1,int(modes)+1):
            # two orthogonal traveling-phase shapes per mode, bounded to keep dimension moderate
            for frame,phase in [(n,np.cos(k*theta)[:,None]),(b,np.sin(k*theta)[:,None])]:
                arr=np.zeros((total,3));arr[offsets[ci]:offsets[ci+1]]=frame*phase
                norm=np.sqrt(np.mean(np.sum(arr*arr,axis=1))); arr/=max(norm,1e-15);basis.append(arr)
    return np.asarray(basis),offsets

def split_flat(flat,offsets): return [flat[offsets[i]:offsets[i+1]] for i in range(len(offsets)-1)]
def potential_factory(components,core=1.0,modes=2):
    comps=[as_closed(c) for c in components]; flat=np.vstack(comps);B,offs=perturbation_basis(comps,modes=modes)
    def U(q):
        q=np.asarray(q,dtype=float); x=flat+np.tensordot(q,B,axes=(0,0));return total_kernel(energy_matrix(split_flat(x,offs),core=core))
    return U,B,offs

def gradient_hessian(U,d,eps=0.01):
    z=np.zeros(d);u0=U(z);g=np.zeros(d);K=np.zeros((d,d))
    for i in range(d):
        ei=np.zeros(d);ei[i]=eps; up=U(ei);um=U(-ei);g[i]=(up-um)/(2*eps);K[i,i]=(up-2*u0+um)/(eps*eps)
    for i in range(d):
        for j in range(i+1,d):
            ei=np.zeros(d);ej=np.zeros(d);ei[i]=eps;ej[j]=eps
            v=(U(ei+ej)-U(ei-ej)-U(-ei+ej)+U(-ei-ej))/(4*eps*eps);K[i,j]=K[j,i]=v
    return u0,g,K

def mass_matrix(d,scale=1.0): return np.eye(d)*float(scale)
def jacobian(M,K,G=None):
    M=np.asarray(M,dtype=float);K=np.asarray(K,dtype=float);d=len(M);G=np.zeros_like(K) if G is None else np.asarray(G,dtype=float);Mi=np.linalg.inv(M)
    return np.block([[np.zeros((d,d)),np.eye(d)],[-Mi@K,-Mi@G]])
def spectrum(M,K,G=None):
    J=jacobian(M,K,G);lam=np.linalg.eigvals(J);freq=sorted([abs(z.imag) for z in lam if abs(z.imag)>1e-9 and abs(z.real)<=max(1e-7,0.05*abs(z.imag))])
    # remove plus/minus duplicates
    uniq=[]
    for f in freq:
        if not uniq or abs(f-uniq[-1])/max(f,uniq[-1],1e-30)>1e-5:uniq.append(float(f))
    return J,lam,uniq

def linear_trajectory(M,K,q0,dt,steps):
    Mi=np.linalg.inv(M);q=np.asarray(q0,dtype=float).copy();v=np.zeros_like(q);out=[]
    def acc(x):return -Mi@(K@x)
    a=acc(q)
    for _ in range(int(steps)):
        out.append(q.copy());q=q+v*dt+0.5*a*dt*dt;an=acc(q);v=v+0.5*(a+an)*dt;a=an
    return np.asarray(out)
def fft_peak(signal,dt):
    x=np.asarray(signal,dtype=float);x=x-x.mean();sp=np.abs(np.fft.rfft(x));fr=np.fft.rfftfreq(len(x),dt)
    if len(sp)<=1:return None
    k=1+int(np.argmax(sp[1:]));return float(2*np.pi*fr[k])

def nonlinear_1d_trajectory(U,mass=1.0,eps_grad=1e-4,q0=0.01,dt=0.01,steps=64):
    def grad(q):return (U(np.array([q+eps_grad]))-U(np.array([q-eps_grad])))/(2*eps_grad)
    q=float(q0);v=0.0;a=-grad(q)/mass;rows=[]
    for _ in range(int(steps)):
        H=.5*mass*v*v+U(np.array([q]));rows.append((q,v,H,a,grad(q)))
        qn=q+v*dt+.5*a*dt*dt;an=-grad(qn)/mass;v=v+.5*(a+an)*dt;q=qn;a=an
    return np.asarray(rows,dtype=float)
