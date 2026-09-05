from __future__ import annotations
import math
import numpy as np
from .constants import DEFAULTS, GAMMA0
from .geometry import trefoil, ring, meridian, curve_length, rescale_to_length, recenter, close_curve
from .kernels import biot_savart_points, line_integral_velocity, gauss_linking, regularized_filament_energy, writhe_midpoint
from .fields import swirl_gaussian_velocity, swirl_gaussian_vorticity, shear_velocity, shear_vorticity, abc_velocity, div_curl, grad_speed2


def _result(test_id,name,status,metrics,gate,notes=None):
    return {"id":test_id,"name":name,"status":status,"metrics":metrics,"gate":gate,"notes":notes or []}


def audit_t01_swirl_tonic(n_loop=2048, radius=0.8, omega0=2.0, L=1.0):
    t=np.linspace(0,2*np.pi,n_loop,endpoint=False)
    loop=np.column_stack([radius*np.cos(t),radius*np.sin(t),np.zeros_like(t)])
    gamma=line_integral_velocity(loop,lambda p: swirl_gaussian_velocity(p,omega0,L))
    # Independent polar quadrature of vorticity flux
    nr=max(256,n_loop//4); rr=(np.arange(nr)+0.5)*radius/nr
    dr=radius/nr
    pts=np.column_stack([rr,np.zeros(nr),np.zeros(nr)])
    wz=swirl_gaussian_vorticity(pts,omega0,L)[:,2]
    flux=float(np.sum(wz*2*np.pi*rr*dr))
    exact=math.pi*omega0*radius**2*math.exp(-radius**2/L**2)
    probes=np.array([[0.23,0.17,0.1],[-0.41,0.31,-0.2],[0.52,-0.25,0.3]])
    div,curl=div_curl(lambda p: swirl_gaussian_velocity(p,omega0,L),probes,1e-5)
    curl_exact=swirl_gaussian_vorticity(probes,omega0,L)
    stokes_rel=abs(gamma-flux)/max(abs(exact),1e-30)
    curl_rel=float(np.linalg.norm(curl-curl_exact)/max(np.linalg.norm(curl_exact),1e-30))
    div_rel=float(np.linalg.norm(div)*L/max(np.linalg.norm(swirl_gaussian_velocity(probes,omega0,L)),1e-30))
    ok=stokes_rel<DEFAULTS['stokes_rel'] and curl_rel<1e-7 and div_rel<1e-7
    return _result('T01','material swirl-tonic / Stokes', 'PASS' if ok else 'FAIL',
        {"line_circulation":gamma,"surface_vorticity_flux":flux,"exact":exact,"stokes_rel":stokes_rel,"curl_rel":curl_rel,"div_rel":div_rel},
        {"stokes_rel_max":DEFAULTS['stokes_rel'],"curl_rel_max":1e-7,"div_rel_max":1e-7})


def audit_t02_holonomy(curve=None,gamma=GAMMA0,core_a=None,probe_radius=None,n_probe=512):
    c=trefoil(800) if curve is None else close_curve(curve)
    L=curve_length(c); mean_edge=L/len(c)
    if core_a is None: core_a=0.20*mean_edge
    if probe_radius is None: probe_radius=max(8*core_a,3*mean_edge)
    loop=meridian(c,probe_radius,n_probe,index=len(c)//7)
    lk=gauss_linking(loop,c)
    f=lambda p: biot_savart_points(p,c,gamma=gamma,core_a=core_a)
    circ=line_integral_velocity(loop,f)
    top=gamma*lk
    rel=abs(circ-top)/max(abs(top),1e-30)
    # orientation control
    loop_rev=loop[::-1].copy(); lk_rev=gauss_linking(loop_rev,c); circ_rev=line_integral_velocity(loop_rev,f)
    sign_err=abs(circ+circ_rev)/max(abs(circ),1e-30)+abs(lk+lk_rev)/max(abs(lk),1e-30)
    ok=rel<DEFAULTS['holonomy_rel'] and sign_err<1e-6 and abs(abs(lk)-1)<0.05
    return _result('T02','circulation topological holonomy','PASS' if ok else 'FAIL',
        {"gamma_input":gamma,"gauss_linking":lk,"circulation":circ,"topological_target":top,"holonomy_rel":rel,"orientation_control":sign_err,"probe_radius":probe_radius,"core_a":core_a},
        {"holonomy_rel_max":DEFAULTS['holonomy_rel'],"abs_linking_target":1.0})


def _rectangle(L,H,y0,t,U,n_side):
    yb=y0+U*t; yt=yb+H
    x=np.linspace(0,L,n_side,endpoint=False); y=np.linspace(yb,yt,n_side,endpoint=False)
    a=np.column_stack([x,np.full_like(x,yb),np.zeros_like(x)])
    b=np.column_stack([np.full_like(y,L),y,np.zeros_like(y)])
    c=np.column_stack([x[::-1]+L/n_side,np.full_like(x,yt),np.zeros_like(x)])
    d=np.column_stack([np.zeros_like(y),y[::-1]+H/n_side,np.zeros_like(y)])
    return np.vstack([a,b,c,d])


def audit_t03_moving_loop(a=0.7,L=1.3,H=0.8,y0=0.4,U=0.25,n_side=1000,dt=1e-4):
    def circ(t): return line_integral_velocity(_rectangle(L,H,y0,t,U,n_side),lambda p:shear_velocity(p,a))
    dnum=(circ(dt)-circ(-dt))/(2*dt)
    loop=_rectangle(L,H,y0,0,U,n_side)
    p=close_curve(loop); q=np.roll(p,-1,axis=0); mid=0.5*(p+q); dl=q-p
    v=shear_velocity(mid,a); w=shear_vorticity(mid,a); uc=np.tile([0,U,0],(len(mid),1))
    rhs=float(np.einsum('ij,ij->i',np.cross(v-uc,w),dl).sum())
    exact=-2*a*L*H*U
    rel=max(abs(dnum-exact),abs(rhs-exact))/max(abs(exact),1e-30)
    ok=rel<DEFAULTS['moving_loop_rel']
    return _result('T03','moving-loop relative-motion identity','PASS' if ok else 'FAIL',
        {"dGamma_dt_numeric":dnum,"rhs_loop_integral":rhs,"exact":exact,"relative_error":rel},
        {"relative_error_max":DEFAULTS['moving_loop_rel']})


def _fibonacci_sphere(n,r):
    i=np.arange(n); phi=(1+5**0.5)/2
    z=1-2*(i+0.5)/n; th=2*np.pi*i/phi
    xy=np.sqrt(np.maximum(0,1-z*z))
    return r*np.column_stack([xy*np.cos(th),xy*np.sin(th),z])


def audit_t04_exterior_hodge(curve=None,gamma=1.7,core_a=None,n_samples=96):
    c=trefoil(600) if curve is None else close_curve(curve)
    scale=np.max(np.linalg.norm(c-c.mean(axis=0),axis=1)); c=recenter(c)
    if core_a is None: core_a=0.01*scale
    pts=_fibonacci_sphere(n_samples,2.5*scale)
    unit=lambda p:biot_savart_points(p,c,1.0,core_a)
    h=unit(pts)
    nuisance=np.array([0.013,-0.021,0.008])
    vsyn=gamma*h+nuisance
    A=np.zeros((3*len(pts),4)); A[:,0]=h.reshape(-1)
    for j in range(3): A[j::3,j+1]=1.0
    coef,*_=np.linalg.lstsq(A,vsyn.reshape(-1),rcond=None)
    fit=(A@coef).reshape(-1,3)
    fit_rel=float(np.linalg.norm(fit-vsyn)/np.linalg.norm(vsyn))
    gamma_rel=abs(coef[0]-gamma)/abs(gamma)
    # exterior differential audit on actual topological field
    hstep=1e-4*scale
    div,curl=div_curl(unit,pts[:24],hstep)
    v0=unit(pts[:24]); vscale=max(np.sqrt(np.mean(np.sum(v0*v0,axis=1))),1e-30)
    curl_rel=float(np.sqrt(np.mean(np.sum(curl*curl,axis=1)))*scale/vscale)
    div_rel=float(np.sqrt(np.mean(div*div))*scale/vscale)
    ok=fit_rel<1e-10 and gamma_rel<1e-10 and curl_rel<DEFAULTS['exterior_curl_rel'] and div_rel<DEFAULTS['exterior_div_rel']
    return _result('T04','exterior harmonic/Hodge sector','PASS' if ok else 'FAIL',
        {"gamma_true":gamma,"gamma_fit":float(coef[0]),"gamma_fit_rel":gamma_rel,"fit_rel":fit_rel,"curl_rel":curl_rel,"div_rel":div_rel,"nuisance_true":nuisance.tolist(),"nuisance_fit":coef[1:].tolist()},
        {"gamma_fit_rel_max":1e-10,"fit_rel_max":1e-10,"curl_rel_max":DEFAULTS['exterior_curl_rel'],"div_rel_max":DEFAULTS['exterior_div_rel']})


def audit_t05_energy_helicity(curve=None,core_a=None,n_pert=12,seed=12345):
    # Positive-control Beltrami field
    rng=np.random.default_rng(seed); pts=rng.uniform(0,2*np.pi,size=(64,3))
    div,curl=div_curl(abc_velocity,pts,1e-5); v=abc_velocity(pts)
    lam=float(np.einsum('ij,ij->',v,curl)/np.einsum('ij,ij->',v,v))
    bel_rel=float(np.linalg.norm(curl-lam*v)/np.linalg.norm(curl))
    div_rel=float(np.linalg.norm(div)/np.linalg.norm(v))
    metrics={"beltrami_lambda":lam,"beltrami_rel":bel_rel,"beltrami_div_rel":div_rel}
    notes=[]
    if curve is not None:
        c=close_curve(curve); L=curve_length(c); mean=L/len(c)
        if core_a is None: core_a=2*mean
        E0=regularized_filament_energy(c,1.0,1.0,core_a); W0=writhe_midpoint(c)
        eps=0.15*mean
        dE=[]; dH=[]
        t=np.arange(len(c))/len(c)*2*np.pi
        for k in range(n_pert):
            modes=rng.integers(1,7,size=3); phase=rng.uniform(0,2*np.pi,size=3)
            d=np.column_stack([np.sin(modes[j]*t+phase[j]) for j in range(3)])
            d-=d.mean(axis=0); d/=max(np.sqrt(np.mean(np.sum(d*d,axis=1))),1e-30)
            cp=rescale_to_length(c+eps*d,L); cm=rescale_to_length(c-eps*d,L)
            Ep=regularized_filament_energy(cp,1.0,1.0,core_a); Em=regularized_filament_energy(cm,1.0,1.0,core_a)
            Wp=writhe_midpoint(cp); Wm=writhe_midpoint(cm)
            dE.append((Ep-Em)/(2*eps)); dH.append((Wp-Wm)/(2*eps)) # gamma=1 => H~Wr for fixed twist
        dE=np.asarray(dE); dH=np.asarray(dH)
        denom=float(np.dot(dH,dH))
        if denom>1e-20:
            lamH=float(np.dot(dH,dE)/denom); resid=float(np.linalg.norm(dE-lamH*dH)/max(np.linalg.norm(dE),1e-30))
        else:
            lamH=float('nan'); resid=float('nan')
        metrics.update({"centerline_E0_normalized":E0,"centerline_writhe0":W0,"stationarity_lambda":lamH,"stationarity_residual":resid,"core_a":core_a,"perturbations":n_pert})
        notes.append('Centerline stationarity is a research diagnostic; failure does not invalidate the orthodox Beltrami positive control or SST as a whole.')
    ok=bel_rel<DEFAULTS['beltrami_rel'] and div_rel<1e-8
    return _result('T05','energy--helicity stationarity','PASS' if ok else 'FAIL',metrics,
        {"beltrami_rel_max":DEFAULTS['beltrami_rel'],"beltrami_div_rel_max":1e-8,"centerline_stationarity":"report-only unless preregistered"},notes)


def _cycle_work(K,n=4000):
    t=np.linspace(0,2*np.pi,n,endpoint=False); q=np.column_stack([1.3*np.cos(t),0.7*np.sin(t)])
    F=q@K.T; dq=np.roll(q,-1,axis=0)-q; Fmid=0.5*(F+np.roll(F,-1,axis=0))
    W=float(np.einsum('ij,ij->i',Fmid,dq).sum())
    scale=float(np.max(np.linalg.norm(F,axis=1))*np.max(np.linalg.norm(q,axis=1)))
    return W,W/max(scale,1e-30)


def audit_t06_cyclic_work():
    Ks=np.array([[2.1,0.35],[0.35,1.4]])
    Ka=np.array([[0,0.4],[-0.4,0]])
    Wp,Rp=_cycle_work(Ks); Wn,Rn=_cycle_work(Ks+Ka)
    asym_pass=float(np.linalg.norm(Ks-Ks.T)/max(np.linalg.norm(Ks),1e-30))
    asym_fail=float(np.linalg.norm((Ks+Ka)-(Ks+Ka).T)/np.linalg.norm(Ks+Ka))
    ok=abs(Rp)<DEFAULTS['cyclic_work_rel'] and abs(Rn)>1e-3
    return _result('T06','cyclic-work / chirality response','PASS' if ok else 'FAIL',
        {"conservative_cycle_work":Wp,"conservative_work_rel":Rp,"nonconservative_cycle_work":Wn,"nonconservative_work_rel":Rn,"symmetric_asymmetry_ratio":asym_pass,"antisymmetric_control_ratio":asym_fail},
        {"conservative_work_rel_max":DEFAULTS['cyclic_work_rel'],"negative_control_min_abs":1e-3},
        ['The antisymmetric negative control must fail the conservative gate; this is a software discriminability check.'])


def audit_t07_radial_flux(curve=None,core_a=None,radii=None,n_sphere=120):
    c=ring(500,1.0) if curve is None else recenter(close_curve(curve))
    scale=np.max(np.linalg.norm(c,axis=1))
    if core_a is None: core_a=0.02*scale
    if radii is None: radii=np.array([4.0,5.0,6.5,8.0,10.0])*scale
    means=[]; rms=[]; flux=[]; coherence=[]
    field=lambda p:biot_savart_points(p,c,1.0,core_a)
    for r in radii:
        pts=_fibonacci_sphere(n_sphere,float(r)); nvec=pts/r
        g=0.5*grad_speed2(field,pts,1e-3*r)
        gr=np.einsum('ij,ij->i',g,nvec)
        m=float(np.mean(gr)); rr=float(np.sqrt(np.mean(gr*gr)))
        means.append(m); rms.append(rr); flux.append(4*np.pi*r*r*m); coherence.append(abs(m)/max(rr,1e-30))
    radii=np.asarray(radii,float); rms=np.asarray(rms); flux=np.asarray(flux); coherence=np.asarray(coherence)
    mask=rms>0
    slope=np.polyfit(np.log(radii[mask]),np.log(rms[mask]),1)[0] if np.sum(mask)>=2 else np.nan
    exponent=float(-slope)
    fmean=float(np.mean(flux)); fcv=float(np.std(flux)/max(abs(fmean),np.max(np.abs(flux))*1e-12,1e-30))
    coh=float(np.mean(coherence))
    newton_ok=coh>DEFAULTS['radial_coherence'] and abs(exponent-2)<DEFAULTS['radial_exponent_tol'] and fcv<DEFAULTS['radial_flux_cv']
    status='PASS' if newton_ok else 'REJECTED_NEGATIVE_CONTROL'
    return _result('T07','derived radial force-flux',status,
        {"radii":radii.tolist(),"mean_gr":means,"rms_gr":rms.tolist(),"signed_flux":flux.tolist(),"mean_radial_coherence":coh,"rms_decay_exponent":exponent,"signed_flux_cv":fcv},
        {"radial_coherence_min":DEFAULTS['radial_coherence'],"exponent_target":2.0,"exponent_tolerance":DEFAULTS['radial_exponent_tol'],"flux_cv_max":DEFAULTS['radial_flux_cv']},
        ['Built-in compact-vortex Bernoulli-pressure candidate is expected to be rejected; this is the intended Maxwell-1/r exclusion control.'])


def run_demo(curve=None):
    return [audit_t01_swirl_tonic(),audit_t02_holonomy(curve),audit_t03_moving_loop(),audit_t04_exterior_hodge(curve),audit_t05_energy_helicity(curve),audit_t06_cyclic_work(),audit_t07_radial_flux(curve)]
