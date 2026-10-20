"""Dimensionless analytic control kernels; zero empirical Casimir/SST target constants.

IMPORTANT: D01/D02/D03 are synthetic controls, not PKLSA certification.
"""
from __future__ import annotations
import math


def dot(a,b): return sum(x*y for x,y in zip(a,b))
def matvec(a,x): return [dot(r,x) for r in a]
def matmul(a,b): return [[sum(a[i][k]*b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]
def norm2(x): return dot(x,x)
def strain(g): return [[0.5*(g[i][j]+g[j][i]) for j in range(3)] for i in range(3)]
def vorticity(g): return [g[2][1]-g[1][2],g[0][2]-g[2][0],g[1][0]-g[0][1]]
def trace(g): return sum(g[i][i] for i in range(len(g)))

def euler_snapshot(case):
    g=case['gradient']; x=case['point']; rho=case['rho']; c=case['c_star']
    u=matvec(g,x); om=vorticity(g); s=strain(g); gg=matmul(g,g)
    rhs=rho*(0.5*norm2(om)-sum(norm2(row) for row in s))
    p_laplacian=-rho*trace(gg)
    pgrad=[-rho*z for z in matvec(gg,x)]
    N=math.sqrt(1.0-norm2(u)/c**2)
    return dict(velocity=u,divergence=trace(g),omega=om,omega2=norm2(om),strain2=sum(norm2(r) for r in s),pressure_poisson_rhs=rhs,pressure_laplacian=p_laplacian,pressure_gradient=pgrad,clock_N=N)


def phase_path(dataset, path):
    theta=dataset['theta']; edges=dataset['edges']; acc=theta[path[-1]]-theta[path[0]]
    for a,b in zip(path,path[1:]):
        e=next((e for e in edges if e['i']==a and e['j']==b),None)
        if e is None: raise ValueError('path not supported by oriented graph')
        acc-=e['vartheta']
    return acc


def phase_path_rate(dataset,path):
    omega0=dataset['omega0']; N=dataset['clock_N']; Es={(e['i'],e['j']):e['E'] for e in dataset['edges']}
    return omega0[path[-1]]*N[path[-1]]-omega0[path[0]]*N[path[0]]+sum(Es[(a,b)] for a,b in zip(path,path[1:]))


def direct_phase_rate(dataset,path):
    edges=dataset['edges']; phi=dataset['phi']; deriv_theta=[dataset['omega0'][i]*dataset['clock_N'][i]-phi[i] for i in range(len(phi))]
    rate=deriv_theta[path[-1]]-deriv_theta[path[0]]
    for a,b in zip(path,path[1:]):
        e=next(e for e in edges if e['i']==a and e['j']==b)
        # E = -dot_vartheta - (phi_j - phi_i)
        dot_vartheta=-e['E']-(phi[b]-phi[a]);rate-=dot_vartheta
    return rate


def gauge_transform(dataset,chi):
    import copy
    d=copy.deepcopy(dataset)
    d['theta']=[t+z for t,z in zip(dataset['theta'],chi)]
    for e in d['edges']: e['vartheta']+=chi[e['j']]-chi[e['i']]
    # static gauge shift; temporal gauge for dynamic tests is covered by rate formula
    return d


def susceptibility(surface,omega_imag):
    """b^T (K + xi^2 M)^-1 b, analytic 2x2 static matrix."""
    xi=omega_imag; k=surface['K']; m=surface['M']; b=surface['b']
    a=k[0][0]+xi*xi*m[0]; d=k[1][1]+xi*xi*m[1]; off=k[0][1]
    det=a*d-off*off
    if a<=0 or det<=0: raise ValueError('nonpositive stable oscillator Hessian')
    return (d*b[0]**2-2*off*b[0]*b[1]+a*b[1]**2)/det


def effective_stiffness(surface,xi=0.0):
    """Toy scalar delta-sheet coefficient; bare part is an explicit model assumption."""
    if surface['kind']=='decoupled':return 0.0
    return surface['lambda_bare']-susceptibility(surface,xi)


def reflection(surface,k):
    lam=effective_stiffness(surface)
    if lam < 0:raise ValueError('toy sheet unstable / negative stiffness')
    return 0.0 if lam==0 else lam/(2.0*k+lam)


def simpson(f,a,b,n=1800):
    if n%2:raise ValueError('even Simpson intervals required')
    h=(b-a)/n
    val=f(a)+f(b)
    for i in range(1,n):val+=(4.0 if i%2 else 2.0)*f(a+h*i)
    return h*val/3.0


def free_energy_area(a,T,s1,s2,n=1800):
    """Classical scalar Gaussian toy, dimensionless k_B=1; NOT quantum Casimir."""
    # x=t^2 smooths the integrable x*log(x) cusp near x=0.
    def fn(t):
        if t==0.0:return 0.0
        x=t*t;k=x/a
        q=reflection(s1,k)*reflection(s2,k)*math.exp(-2*x)
        return 2*t**3*math.log1p(-q)
    return T/(4*math.pi*a*a)*simpson(fn,0.0,math.sqrt(24.0),n)


def pressure_traction(a,T,s1,s2,n=1800):
    """Momentum/stress spectral reconstruction, not a finite-difference of energy."""
    def fn(t):
        if t==0.0:return 0.0
        x=t*t;k=x/a
        q=reflection(s1,k)*reflection(s2,k)*math.exp(-2*x)
        return 2*t**5*q/(1.0-q)
    return -T/(2*math.pi*a**3)*simpson(fn,0.0,math.sqrt(24.0),n)


def pressure_finite_diff(a,T,s1,s2,n=1800):
    h=a*0.001
    f=lambda aa:free_energy_area(aa,T,s1,s2,n)
    # independent derivative, fourth-order
    return -(-f(a+2*h)+8*f(a+h)-8*f(a-h)+f(a-2*h))/(12*h)


def slope_powerlaw(rows):
    vals=[(math.log(r['distance']), math.log(-r['stress_pressure'])) for r in rows if r['stress_pressure'] < -1e-14]
    if len(vals)<3:return None
    mx=sum(x for x,_ in vals)/len(vals);my=sum(y for _,y in vals)/len(vals)
    b=sum((x-mx)*(y-my) for x,y in vals)/sum((x-mx)**2 for x,_ in vals)
    return -b
