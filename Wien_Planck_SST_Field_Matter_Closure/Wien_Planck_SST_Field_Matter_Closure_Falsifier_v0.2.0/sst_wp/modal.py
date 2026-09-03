from __future__ import annotations
import numpy as np, math
from .common import linfit

def kabsch_align(P,Q):
    P=P-P.mean(0);Q=Q-Q.mean(0);H=P.T@Q;U,S,Vt=np.linalg.svd(H);R=Vt.T@U.T
    if np.linalg.det(R)<0: Vt[-1]*=-1;R=Vt.T@U.T
    return P@R

def aligned_displacement(snaps,base):
    out=[]
    for X in snaps: out.append((kabsch_align(X,base)- (base-base.mean(0))).reshape(-1))
    return np.asarray(out)

def pod_freeze(odd,discovery_fraction=0.4):
    n=max(8,int(len(odd)*discovery_fraction)); D=odd[:n]; mu=D.mean(0);U,S,Vt=np.linalg.svd(D-mu,full_matrices=False);phi=Vt[0];coef=(odd-mu)@phi
    frac=float(S[0]**2/max(np.sum(S*S),1e-300)); return phi,mu,coef,n,frac

def dominant_frequency(times,coef,start):
    t=np.asarray(times)[start:];a=np.asarray(coef)[start:];
    if len(t)<16:return {'frequency':float('nan'),'omega':float('nan'),'spectral_power':0,'cycles':0,'period_cv':float('inf'),'harmonic_r2':0}
    dt=float(np.median(np.diff(t)));a=a-np.mean(a);win=np.hanning(len(a));Y=np.fft.rfft(a*win);f=np.fft.rfftfreq(len(a),dt);P=np.abs(Y)**2;P[0]=0;i=int(np.argmax(P));freq=float(f[i]);
    if 0<i<len(P)-1 and P[i-1]>0 and P[i]>0 and P[i+1]>0:
        y0,y1,y2=np.log(P[i-1]),np.log(P[i]),np.log(P[i+1]);den=y0-2*y1+y2
        if abs(den)>1e-15:
            delta=max(-0.5,min(0.5,0.5*(y0-y2)/den));freq=float((i+delta)*(f[1]-f[0]))
    spec=float(P[i]/max(P.sum(),1e-300));cycles=freq*(t[-1]-t[0])
    # simple sine/cos fit
    A=np.column_stack([np.sin(2*np.pi*freq*t),np.cos(2*np.pi*freq*t),np.ones_like(t)]);q=np.linalg.lstsq(A,a,rcond=None)[0];pred=A@q;sst=np.sum((a-a.mean())**2);r2=float(1-np.sum((a-pred)**2)/sst) if sst>0 else 0
    # zero-crossing period CV
    z=np.where(np.diff(np.signbit(a)))[0]; periods=[]
    if len(z)>=5:
        tz=t[z]; periods=np.diff(tz[::2]); pcv=float(np.std(periods)/np.mean(periods)) if len(periods)>1 and np.mean(periods)>0 else float('inf')
    else: pcv=float('inf')
    return {'frequency':freq,'omega':2*np.pi*freq,'spectral_power':spec,'cycles':float(cycles),'period_cv':pcv,'harmonic_r2':r2}
