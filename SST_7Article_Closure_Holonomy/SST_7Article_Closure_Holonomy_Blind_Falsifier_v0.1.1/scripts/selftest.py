from pathlib import Path
import sys,tempfile,json,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sst7.geometry import curve_length,resample_closed,gauss_linking
from sst7.phase import winding
from sst7.pressure import poisson_residual,green_relative
from sst7.representation import even_odd
try:
    from native_ext import native
except Exception: native=None

# geometry + native parity
th=np.linspace(0,2*np.pi,257,endpoint=False); c=np.c_[np.cos(th),np.sin(th),0*th]
L=curve_length(c); assert abs(L-2*np.pi)<2e-3, L
if native is not None:
    Ln=native.curve_length(c); assert abs(Ln-L)<1e-10,(Ln,L)
# Hopf-link Gauss integral and native parity
s=np.linspace(0,2*np.pi,512,endpoint=False)
h1=np.c_[np.cos(s),np.sin(s),0*s]
h2=np.c_[0.5+np.cos(s),0*s,np.sin(s)]
lk=gauss_linking(h1,h2); assert abs(abs(lk)-1)<3e-3,lk
if native is not None:
    lkn=native.gauss_linking(h1,h2); assert abs(lkn-lk)<1e-10,(lkn,lk)
# phase winding
phi=3*th; assert abs(winding(phi)-3)<1e-10
# Taylor-Green periodic Euler pressure Poisson
N=48; x=np.arange(N)*2*np.pi/N; X,Y,Z=np.meshgrid(x,x,x,indexing='ij')
v=np.empty((N,N,N,3)); v[...,0]=np.sin(X)*np.cos(Y); v[...,1]=-np.cos(X)*np.sin(Y); v[...,2]=0
pi=0.25*(np.cos(2*X)+np.cos(2*Y)); rho=7e-7; p=rho*pi
pr=poisson_residual(v,p,2*np.pi/N,rho,'periodic'); assert pr['relative']<0.03,pr['relative']
gr=green_relative(pr['source'],pr['pi'],2*np.pi/N); assert gr<0.03,gr
# even/odd exact decomposition
q=np.linspace(-1,1,100); plus=q*q+0.3*q; minus=q*q-0.3*q; eo=even_odd(plus,minus); assert eo['even_norm']>eo['odd_norm']
print('[SST7] selftest PASS')
print('[SST7] pressure residual',pr['relative'],'green',gr,'native',native is not None)
