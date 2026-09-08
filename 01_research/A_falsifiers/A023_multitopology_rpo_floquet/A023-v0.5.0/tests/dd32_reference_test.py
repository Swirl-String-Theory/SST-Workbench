from __future__ import annotations
import math, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from native_ext.fallback import biot_savart as ref_biot

F=np.float32
class DS:
    __slots__=('hi','lo')
    def __init__(self,hi,lo=0.0): self.hi=F(hi); self.lo=F(lo)

def split(x):
    h=F(x); return DS(h,F(float(x)-float(h)))
def val(x): return float(x.hi)+float(x.lo)
def two_sum(a,b):
    a,b=F(a),F(b); s=F(a+b); bb=F(s-a); e=F(F(a-F(s-bb))+F(b-bb)); return DS(s,e)
def two_prod(a,b):
    a,b=F(a),F(b); p=F(a*b); e=F(math.fma(float(a),float(b),-float(p))); return DS(p,e)
def add(a,b):
    s1=F(a.hi+b.hi); v=F(s1-a.hi); s2=F(F(F(b.hi-v)+F(a.hi-F(s1-v)))+F(a.lo+b.lo)); return two_sum(s1,s2)
def neg(a): return DS(-a.hi,-a.lo)
def sub(a,b): return add(a,neg(b))
def mul(a,b): return add(add(two_prod(a.hi,b.hi),two_prod(a.hi,b.lo)),add(two_prod(a.lo,b.hi),two_prod(a.lo,b.lo)))
def div(a,b):
    q=DS(F(a.hi/b.hi)); r=sub(a,mul(b,q)); q=add(q,DS(F(F(r.hi+r.lo)/b.hi))); r=sub(a,mul(b,q)); return add(q,DS(F(F(r.hi+r.lo)/b.hi)))
def sqrtdd(a):
    y=DS(F(math.sqrt(float(a.hi))))
    for _ in range(2): y=add(y,div(sub(a,mul(y,y)),mul(y,DS(2.0))))
    return y

def ds_biot(p,core=.05,gamma=1.0):
    p=np.asarray(p,float); n=len(p); out=np.zeros_like(p); s=split(gamma/(4*math.pi)); a2=split(core*core)
    for i in range(n):
        xx,yy,zz=map(split,p[i]); vx=DS(0);vy=DS(0);vz=DS(0)
        for j in range(n):
            k=(j+1)%n; ax,ay,az=map(split,p[j]); bx,by,bz=map(split,p[k])
            dlx,dly,dlz=sub(bx,ax),sub(by,ay),sub(bz,az)
            mx,my,mz=mul(add(ax,bx),DS(.5)),mul(add(ay,by),DS(.5)),mul(add(az,bz),DS(.5))
            rx,ry,rz=sub(xx,mx),sub(yy,my),sub(zz,mz)
            D=add(add(mul(rx,rx),mul(ry,ry)),add(mul(rz,rz),a2)); inv=div(DS(1),mul(D,sqrtdd(D))); scale=mul(s,inv)
            vx=add(vx,mul(scale,sub(mul(dly,rz),mul(dlz,ry))))
            vy=add(vy,mul(scale,sub(mul(dlz,rx),mul(dlx,rz))))
            vz=add(vz,mul(scale,sub(mul(dlx,ry),mul(dly,rx))))
        out[i]=[val(vx),val(vy),val(vz)]
    return out

def main():
    rng=np.random.default_rng(7)
    worst={}
    for name in ('add','mul','div','sqrt'):
        ee=[]
        for _ in range(2000):
            a=float(10**rng.uniform(-2,2)*rng.uniform(.7,1.3)); b=float(10**rng.uniform(-2,2)*rng.uniform(.7,1.3)); A=split(a);B=split(b)
            if name=='add': z,ref=add(A,B),a+b
            elif name=='mul': z,ref=mul(A,B),a*b
            elif name=='div': z,ref=div(A,B),a/b
            else: z,ref=sqrtdd(A),math.sqrt(a)
            ee.append(abs(val(z)-ref)/max(abs(ref),1e-300))
        worst[name]=max(ee)
        assert worst[name] < 5e-13,(name,worst[name])
    n=36;t=np.linspace(0,2*np.pi,n,endpoint=False)
    p=np.c_[(2+.55*np.cos(3*t))*np.cos(2*t),(2+.55*np.cos(3*t))*np.sin(2*t),.55*np.sin(3*t)];p/=np.sqrt(np.mean(np.sum(p*p,axis=1)))
    r=ref_biot(p,p,1.0,.05); d=ds_biot(p,.05); rel=float(np.linalg.norm(d-r)/np.linalg.norm(r))
    assert rel<1e-11,rel
    print({'ok':True,'worst_scalar_relative':worst,'biot_relative_l2':rel})
    return 0
if __name__=='__main__': raise SystemExit(main())
