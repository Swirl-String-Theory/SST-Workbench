from __future__ import annotations
import numpy as np
from scipy.linalg import eig
from .profiles import profile,profile_metrics

EPS=1e-14

def chebyshev_collocation(N,rmax):
    N=int(N); rmax=float(rmax)
    if N<8: raise ValueError("radial_n must be >=8")
    j=np.arange(N); x=np.cos(np.pi*j/(N-1)); c=np.ones(N); c[[0,-1]]=2; c=c*((-1.0)**j)
    X=np.tile(x,(N,1)).T; dX=X-X.T; D=np.outer(c,1/c)/(dX+np.eye(N)); D=D-np.diag(np.sum(D,axis=1))
    r=(1-x)*rmax/2.0; Dr=(-2.0/rmax)*D
    return r,Dr

def build_generalized(profile_name,axial_ratio,m,k_hat,radial_n=40,rmax=5.0):
    N=int(radial_n); r,D=chebyshev_collocation(N,rmax); re=r.copy(); re[0]=max(.5*r[1],1e-10); U,V=profile(profile_name,r,axial_ratio); Up=D@U; Vp=D@V; adv=m*V/re+float(k_hat)*U
    M=4*N; A=np.zeros((M,M),complex); B=np.zeros((M,M),complex)
    for i in range(N):
        A[i,i]=-1j*adv[i]; A[i,N+i]=2*V[i]/re[i]; A[i,3*N:4*N]-=D[i]; B[i,i]=1
        row=N+i; A[row,i]=-(Vp[i]+V[i]/re[i]); A[row,N+i]=-1j*adv[i]; A[row,3*N+i]=-1j*m/re[i]; B[row,N+i]=1
        row=2*N+i; A[row,i]=-Up[i]; A[row,2*N+i]=-1j*adv[i]; A[row,3*N+i]=-1j*float(k_hat); B[row,2*N+i]=1
        row=3*N+i; A[row,0:N]+=D[i]; A[row,i]+=1/re[i]; A[row,N+i]+=1j*m/re[i]; A[row,2*N+i]+=1j*float(k_hat)
    def clear(row): A[row,:]=0; B[row,:]=0
    if abs(int(m))==1:
        clear(0); A[0,0]=1; A[0,N]=1j*np.sign(m)
        clear(N); A[N,0:N]=D[0]; A[N,N:2*N]+=-1j*np.sign(m)*D[0]
        clear(2*N); A[2*N,2*N]=1
        clear(3*N); A[3*N,3*N]=1
    else:
        for row,col in ((0,0),(N,N),(2*N,2*N),(3*N,3*N)): clear(row); A[row,col]=1
    i=N-1
    for row,col in ((i,i),(N+i,N+i),(2*N+i,2*N+i),(3*N+i,3*N+i)): clear(row); A[row,col]=1
    return r,re,U,V,adv,A,B

def solve_spectrum(profile_name,axial_ratio,m,k_hat,radial_n=40,rmax=5.0,max_abs_lambda=50.0):
    r,re,U,V,adv,A,B=build_generalized(profile_name,axial_ratio,m,k_hat,radial_n,rmax); vals,vec=eig(A,B,check_finite=False); good=np.isfinite(vals)&(np.abs(vals)<float(max_abs_lambda)); vals=vals[good]; vec=vec[:,good]; N=len(r); modes=[]
    for j,lam in enumerate(vals):
        q=vec[:,j]; denA=max(np.linalg.norm(A@q),1e-30); resid=float(np.linalg.norm(A@q-lam*(B@q))/denA); ur=q[:N]; ut=q[N:2*N]; uz=q[2*N:3*N]; wt=re
        E=(np.abs(ur)**2+np.abs(ut)**2+np.abs(uz)**2)*wt; den=float(np.sum(E))
        if den<1e-30: continue
        eta=float(np.sum(np.abs(uz)**2*wt)/den); loc=float(np.sum(E[re<=1.0])/den); hybrid=float(4*eta*(1-eta)*loc)
        om=float(-lam.imag); advf=float(np.sum(np.asarray(adv,float)*E)/den); omintr=float(om-advf)
        modes.append({'lambda':complex(lam),'growth':float(lam.real),'omega':om,'advective_frequency':advf,'omega_intrinsic':omintr,'residual':resid,'axial_energy_fraction':eta,'core_localization':loc,'hybrid_score':hybrid,'vector':q})
    return {'r':r,'U':U,'V':V,'profile_metrics':profile_metrics(r,U,V),'modes':modes}

def _admissible(x,min_localization=.35,min_axial=.05,max_axial=.95,max_residual=1e-7):
    return bool(x is not None and x['residual']<=max_residual and x['core_localization']>=min_localization and min_axial<=x['axial_energy_fraction']<=max_axial and np.isfinite(x['omega']))

def select_hybrid_mode(spec,min_localization=.35,min_axial=.05,max_axial=.95,max_residual=1e-7):
    cand=[x for x in spec['modes'] if _admissible(x,min_localization,min_axial,max_axial,max_residual)]
    if not cand: return None
    return max(cand,key=lambda x:(max(x['growth'],0.0),x['hybrid_score'],x['core_localization'],-x['residual']))

def vector_overlap(a,b):
    if a is None or b is None:return 0.0
    x=np.asarray(a['vector']); y=np.asarray(b['vector']); return float(abs(np.vdot(x,y))/(max(np.linalg.norm(x)*np.linalg.norm(y),1e-30)))

def track_mode(reference,spec,min_overlap=.10,max_residual=1e-7):
    cand=[x for x in spec['modes'] if x['residual']<=max_residual]
    if not cand:return None
    z=max(cand,key=lambda x:vector_overlap(reference,x)); return z if vector_overlap(reference,z)>=min_overlap else None

def mode_at_axial(profile_name,target_axial,m,k_hat,radial_n,rmax,sel_cfg):
    """Optionally continue one eigenbranch from a preregistered axial-flow anchor.

    This prevents the selector from silently jumping between the fast swirl-locked
    and slow branches as U_s/V_theta is scanned.
    """
    kw={k:v for k,v in sel_cfg.items() if k in ('min_localization','min_axial','max_axial','max_residual')}
    if not bool(sel_cfg.get('branch_continuation_enabled',False)):
        sp=solve_spectrum(profile_name,target_axial,m,k_hat,radial_n,rmax); return select_hybrid_mode(sp,**kw),{'enabled':False,'target_axial_ratio':float(target_axial)}
    anchor=float(sel_cfg.get('branch_anchor_axial_ratio',-1.0)); nstep=max(2,int(sel_cfg.get('branch_axial_steps',7))); minov=float(sel_cfg.get('branch_min_overlap',sel_cfg.get('min_overlap',.08))); maxres=float(sel_cfg.get('max_residual',1e-7))
    path=np.linspace(anchor,float(target_axial),nstep) if abs(float(target_axial)-anchor)>1e-14 else np.array([anchor])
    sp=solve_spectrum(profile_name,float(path[0]),m,k_hat,radial_n,rmax); md=select_hybrid_mode(sp,**kw)
    hist=[]
    if md is None:return None,{'enabled':True,'anchor_axial_ratio':anchor,'target_axial_ratio':float(target_axial),'success':False,'reason':'no anchor hybrid mode','path':hist}
    hist.append({'axial_ratio':float(path[0]),'overlap_from_previous':1.0,'omega':float(md['omega']),'growth':float(md['growth'])})
    prev=md
    for mu in path[1:]:
        sp=solve_spectrum(profile_name,float(mu),m,k_hat,radial_n,rmax); nxt=track_mode(prev,sp,minov,maxres)
        ov=vector_overlap(prev,nxt) if nxt is not None else 0.0
        if nxt is None:return None,{'enabled':True,'anchor_axial_ratio':anchor,'target_axial_ratio':float(target_axial),'success':False,'reason':'branch overlap lost','path':hist,'failed_at_axial_ratio':float(mu),'failed_overlap':float(ov)}
        hist.append({'axial_ratio':float(mu),'overlap_from_previous':float(ov),'omega':float(nxt['omega']),'growth':float(nxt['growth'])}); prev=nxt
    if not _admissible(prev,**kw):return None,{'enabled':True,'anchor_axial_ratio':anchor,'target_axial_ratio':float(target_axial),'success':False,'reason':'continued mode not physically admissible at target','path':hist}
    return prev,{'enabled':True,'anchor_axial_ratio':anchor,'target_axial_ratio':float(target_axial),'success':True,'min_overlap':float(min(x['overlap_from_previous'] for x in hist)),'path':hist}

def convergence_mode(profile_name,axial_ratio,m,k_hat,levels,rmax=5.0,sel_cfg=None):
    sel_cfg=sel_cfg or {}; rows=[]
    for N in levels:
        md,cont=mode_at_axial(profile_name,axial_ratio,m,k_hat,int(N),rmax,sel_cfg); pm=profile_metrics(*_profile_uv(profile_name,axial_ratio,int(N),rmax))
        rows.append({'radial_n':int(N),'mode':md,'profile_metrics':pm,'axial_branch_continuation':cont})
    good=[r for r in rows if r['mode'] is not None]
    if not good:return {'levels':rows,'converged':False,'reason':'no hybrid eigenmode'}
    gs=np.array([r['mode']['growth'] for r in good]); gp=np.maximum(gs,0.0); ws=np.array([r['mode']['omega'] for r in good]); wi=np.array([r['mode'].get('omega_intrinsic',np.nan) for r in good]); af=np.array([r['mode'].get('advective_frequency',np.nan) for r in good]); hs=np.array([r['mode']['hybrid_score'] for r in good]); loc=np.array([r['mode']['core_localization'] for r in good]); res=np.array([r['mode']['residual'] for r in good])
    gscale=max(float(np.median(gp)),1e-4); growth_span=float(np.ptp(gp)/gscale) if len(gs)>1 else 0.; wspan=float(np.ptp(ws)/max(abs(float(np.median(ws))),1e-6)) if len(ws)>1 else 0.
    converged=(len(good)==len(levels) and growth_span<=float(sel_cfg.get('growth_rel_span_max',1.0)) and wspan<=float(sel_cfg.get('omega_rel_span_max',.35)))
    return {'levels':rows,'converged':bool(converged),'n_good':len(good),'growth_median':float(np.median(gs)),'growth_positive_median':float(np.median(gp)),'growth_abs_median':float(np.median(np.abs(gs))),'growth_rel_span':growth_span,'omega_median':float(np.median(ws)),'omega_intrinsic_median':float(np.nanmedian(wi)),'advective_frequency_median':float(np.nanmedian(af)),'omega_rel_span':wspan,'hybrid_median':float(np.median(hs)),'localization_median':float(np.median(loc)),'residual_max':float(np.max(res))}

def _profile_uv(profile_name,axial_ratio,N,rmax):
    r,_=chebyshev_collocation(N,rmax); U,V=profile(profile_name,r,axial_ratio); return r,U,V

def dispersion_branch(profile_name,axial_ratio,m,k0,radial_n=44,rmax=5.0,frac_step=.10,nside=3,sel_cfg=None):
    sel_cfg=sel_cfg or {}; dk=max(abs(float(k0))*float(frac_step),float(sel_cfg.get('dispersion_dk_floor',.006))); ks=np.array([k0+j*dk for j in range(-int(nside),int(nside)+1)],float)
    ref,cont=mode_at_axial(profile_name,axial_ratio,m,float(k0),radial_n,rmax,sel_cfg)
    if ref is None:return {'available':False,'reason':'no center hybrid mode','k':ks.tolist(),'axial_branch_continuation':cont}
    rows=[]
    for k in ks:
        sp=solve_spectrum(profile_name,axial_ratio,m,float(k),radial_n,rmax); md=track_mode(ref,sp,float(sel_cfg.get('min_overlap',.08)),float(sel_cfg.get('max_residual',1e-7)))
        rows.append({'k':float(k),'mode':md,'overlap':vector_overlap(ref,md) if md else 0.0})
    good=[x for x in rows if x['mode'] is not None]
    if len(good)<5:return {'available':False,'reason':'branch tracking failed','rows':rows,'axial_branch_continuation':cont}
    kk=np.array([x['k'] for x in good]); ww=np.array([x['mode']['omega'] for x in good]); deg=min(3,len(good)-1); co=np.polyfit(kk-k0,ww,deg); pred=np.polyval(co,kk-k0); ss=float(np.sum((ww-pred)**2)); den=float(np.sum((ww-np.mean(ww))**2)); r2=1-ss/max(den,1e-30); rmse=float(np.sqrt(np.mean((ww-pred)**2))); der=np.polyder(co); vg=float(np.polyval(der,0.0)); return {'available':True,'rows':rows,'poly_coeff':co.tolist(),'dispersion_r2':float(r2),'omega_fit_rmse':rmse,'group_velocity':vg,'center_mode':ref,'dk':dk,'axial_branch_continuation':cont}
