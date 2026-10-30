"""Evidence-first 3D Euler pilot: a torus trefoil + a closed return-flow background loop.

No external forcing, no SST material constants; Gaussian-mollified closed polygon
vorticities on the periodic 3-torus. The shared velocity dynamically back-reacts.
No finite-support or nonlinear stability theorem is claimed. All lengths and
circulations are dimensionless. Periodic images and return limbs are physical
features of THIS simulated problem, not the free-space model.
"""
from __future__ import annotations
import argparse, hashlib, json, math, time
from pathlib import Path
import numpy as np
from scipy import fft as sfft

try:
    from numba import njit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

ROOT = Path(__file__).resolve().parents[1]
BOXSIZE = 6.0
SIGMA = 0.12


def source_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_points(name):
    name = name if name.endswith('.xyz') else name + '.xyz'
    path = ROOT / 'source_data' / name
    pts = np.loadtxt(path, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 3 or len(pts) < 16:
        raise ValueError('Expected N x 3 closed-curve samples')
    if np.min(np.linalg.norm(np.diff(pts, axis=0), axis=1)) <= 1e-12:
        raise ValueError('Degenerate segment')
    return pts, path


def length(points):
    return float(np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1).sum())


def racetrack(return_x=2.0, straight_halfheight=1.3, n_straight=100, n_arc=100):
    """Closed stadium in x-z plane, one vertical branch through x=0,y=0.

    The return branch is x=return_x and cap arcs reach |z|=height+return_x/2.
    Tangents are continuous. Return vorticity is the REQUIRED compensating flux.
    """
    D=return_x; H=straight_halfheight
    # From bottom to top along x=0
    z=np.linspace(-H,H,n_straight,endpoint=False)
    main=np.column_stack((np.zeros(len(z)),np.zeros(len(z)),z))
    th=np.linspace(0,np.pi,n_arc,endpoint=False)
    top=np.column_stack((.5*D*(1-np.cos(th)),np.zeros(len(th)),H+.5*D*np.sin(th)))
    z=np.linspace(H,-H,n_straight,endpoint=False)
    ret=np.column_stack((np.full(len(z),D),np.zeros(len(z)),z))
    th=np.linspace(np.pi,2*np.pi,n_arc,endpoint=False)
    bottom=np.column_stack((.5*D*(1-np.cos(th)),np.zeros(len(th)),-H+.5*D*np.sin(th)))
    out=np.concatenate((main,top,ret,bottom))
    return out


def kgrid(n,box=BOXSIZE):
    k=2*np.pi*sfft.fftfreq(n,d=box/n)
    K=np.meshgrid(k,k,k,indexing='ij')
    return np.stack(K)


# Exact Fourier coefficients of an oriented, piecewise-linear closed curve
# convolved with a periodized isotropic Gaussian. For the polygonal path X(s):
# omega(x) = Gamma * integral dX * G_sigma^periodic(x-X).
# Fourier coefficients equal exp(-sigma^2*k^2/2) * sum_j dX_j
# * exp(-i k·mid_j) * sinc(k·dX_j / (2*pi)).
# Divergence vanishes analytically because each k·dX_j integral is the
# difference of the phase factors at successive polygon vertices.
if HAS_NUMBA:
    @njit(parallel=True,cache=True)
    def _fourier_sum(ks,mids,steps,sigma,scale,box):
        nk=len(ks);nm=len(mids)
        out=np.empty((3,nk),dtype=np.complex128)
        for j in prange(nk):
            kx,ky,kz=ks[j,0],ks[j,1],ks[j,2]
            damp=math.exp(-0.5*sigma*sigma*(kx*kx+ky*ky+kz*kz))
            a=0j;b=0j;c=0j
            for i in range(nm):
                delta=kx*steps[i,0]+ky*steps[i,1]+kz*steps[i,2]
                half=0.5*delta
                si=1.0 if abs(half)<1.e-10 else math.sin(half)/half
                phase=kx*(mids[i,0]+box/2)+ky*(mids[i,1]+box/2)+kz*(mids[i,2]+box/2)
                e=complex(math.cos(phase),-math.sin(phase))*si
                a+=steps[i,0]*e
                b+=steps[i,1]*e
                c+=steps[i,2]*e
            out[0,j]=scale*damp*a
            out[1,j]=scale*damp*b
            out[2,j]=scale*damp*c
        return out


def exact_polygon_fourier(points,n,box=BOXSIZE,sigma=SIGMA,gamma=1.0):
    points=np.asarray(points,dtype=np.float64)
    steps=np.roll(points,-1,axis=0)-points
    mids=points+0.5*steps
    ks=kgrid(n,box).reshape(3,-1).T.copy()
    fac=gamma*(n/box)**3
    if HAS_NUMBA:
        vals=_fourier_sum(ks,mids,steps,sigma,fac,box)
    else:
        vals=np.zeros((3,len(ks)),dtype=complex)
        for j in range(0,len(ks),256):
            q=ks[j:j+256]; dot=q@steps.T; phase=q@(mids+box/2).T
            v=np.exp(-1j*phase)*np.sinc(dot/(2*np.pi))
            vals[:,j:j+256] = (v@steps).T*(fac*np.exp(-.5*sigma*sigma*np.sum(q*q,axis=1)))[None,:]
    return vals.reshape(3,n,n,n)


class EulerGrid:
    def __init__(self,n,box=BOXSIZE):
        self.n=n;self.box=float(box);self.dx=box/n
        self.K=kgrid(n,box)
        self.k2=np.sum(self.K*self.K,axis=0)
        self.safe_k2=np.where(self.k2>0,self.k2,1.)
        indices=np.abs(sfft.fftfreq(n)*n)
        mask=(indices[:,None,None]<n/3)&(indices[None,:,None]<n/3)&(indices[None,None,:]<n/3)
        self.filter=mask
        self.local=np.arange(n)*self.dx-box/2

    def fwd(self,x): return sfft.fftn(x,axes=(-3,-2,-1),workers=1)
    def inv(self,x): return sfft.ifftn(x,axes=(-3,-2,-1),workers=1).real

    def project(self,wh):
        dot=np.einsum('ixyz,ixyz->xyz',self.K,wh)
        return (wh-self.K*(dot/self.safe_k2)[None,:,:,:])*self.filter

    def seed(self,points,gamma=1.,sigma=SIGMA):
        raw=exact_polygon_fourier(points,self.n,self.box,sigma,gamma)
        div_raw=np.sqrt(np.sum(np.abs(np.einsum('ixyz,ixyz->xyz',self.K,raw))**2))
        norm=np.sqrt(np.sum(np.abs(raw)**2))
        projected=self.project(raw)
        projection_ratio=float(np.linalg.norm((projected-raw).ravel())/max(1e-30,norm))
        return projected,{'raw_fourier_divergence_ratio':float(div_raw/max(1e-30,norm)),
                          'spectral_projection_correction_ratio':projection_ratio,
                          'zero_mode':float(np.linalg.norm(raw[:,0,0,0]))}

    def velocity(self,w):
        # curl u = omega, div u=0, mean u=0
        k=self.K
        ux=1j*(k[1]*w[2]-k[2]*w[1])/self.safe_k2
        uy=1j*(k[2]*w[0]-k[0]*w[2])/self.safe_k2
        uz=1j*(k[0]*w[1]-k[1]*w[0])/self.safe_k2
        return np.stack((ux,uy,uz))*self.filter

    def curl(self,ah):
        k=self.K
        return 1j*np.stack((k[1]*ah[2]-k[2]*ah[1],
                             k[2]*ah[0]-k[0]*ah[2],
                             k[0]*ah[1]-k[1]*ah[0]))*self.filter

    def rhs(self,fields, frozen_bg=False):
        u=self.inv(self.velocity(np.sum(fields,axis=0)))
        ans=[]
        for idx,f in enumerate(fields):
            if frozen_bg and idx>0:
                ans.append(np.zeros_like(f));continue
            w=self.inv(f)
            cross=np.cross(u,w,axis=0)
            ans.append(self.curl(self.fwd(cross)))
        return np.stack(ans)

    def rk4(self,fields,dt,frozen_bg=False):
        a=self.rhs(fields,frozen_bg)
        b=self.rhs(fields+0.5*dt*a,frozen_bg)
        c=self.rhs(fields+0.5*dt*b,frozen_bg)
        d=self.rhs(fields+dt*c,frozen_bg)
        return (fields+(dt/6)*(a+2*b+2*c+d))*self.filter

    def diagnostics(self,fields,L0,gamma=1.,fit_translation=True):
        k_total=np.sum(fields,axis=0)
        uspec=self.velocity(k_total)
        u=self.inv(uspec)
        rhs=self.rhs(fields)
        # Translation along z is an exact continuous symmetry of this torus.
        # d/dt omega = -U d_z omega => residual R=rhs+U*d_z omega.
        dz_hat=1j*self.K[2][None,None,:,:,:]*fields
        dz=self.inv(dz_hat)
        rhs_physical=self.inv(rhs)
        if fit_translation:
            denom=float(np.vdot(dz,dz).real)
            U=-float(np.vdot(dz,rhs_physical).real)/denom if denom>1e-30 else 0.
        else: U=0.
        # Never combine spectral coefficients with real-space derivatives!
        residual=rhs+U*dz_hat
        rms=lambda a:float(np.sqrt(np.mean(np.sum(a*a,axis=0))))
        comp=[]
        for j in range(len(fields)):
            rr=self.inv(residual[j]);ww=self.inv(rhs[j]);dv=self.inv(1j*self.K[0][None,:,:,:]*fields[j])
            div=self.inv(1j*np.einsum('ixyz,ixyz->xyz',self.K,fields[j]))
            r=rms(rr);f=rms(ww)
            comp.append({'component':int(j),'euler_residual_rms':r,
             'relative_to_induced_rms':float(r/max(f,1e-30)),
             'R_star_L0':float(r*L0**4/gamma**2),
             'D_star_L0_max':float(np.max(np.abs(div))*L0**3/abs(gamma)),
             'vorticity_rms':rms(self.inv(fields[j]))})
        vel_rms=float(np.sqrt(np.mean(np.sum(u*u,axis=0))))
        energy=float(.5*np.mean(np.sum(u*u,axis=0))*self.box**3)
        hel=float(np.mean(np.sum(u*self.inv(k_total),axis=0))*self.box**3)
        # Independent *formulation* of Euler stationarity (same discrete velocity):
        # project ((u - U e_z) . grad)u onto divergence-free periodic vector fields.
        # Its vanishing is the stationary momentum equation with pressure eliminated.
        relu=u.copy();relu[2]-=U
        grad_u=self.inv(1j*self.K[:,None,:,:,:]*uspec[None,:,:,:,:])
        adv=np.einsum('jxyz,jixyz->ixyz',relu,grad_u)
        mom=self.inv(self.project(self.fwd(adv)))
        momentum_Rstar=float(rms(mom)*L0**3/gamma**2)
        return {'U_z_fitted':U,'energy':energy,'helicity':hel,'velocity_rms':vel_rms,
                'momentum_projected_R_star':momentum_Rstar,
                'component_residuals':comp,'max_R_star':max(x['R_star_L0'] for x in comp),
                'max_D_star':max(x['D_star_L0_max'] for x in comp)}

    def centroid_bg(self,bh):
        # positive axial core localized near (x,y)=(0,0), at central z slab.
        w=self.inv(bh)[2]
        coords=self.local
        i=np.nonzero(np.abs(coords)<.7)[0]
        j=i
        iz=np.argmin(np.abs(coords))
        slab=w[np.ix_(i,j,np.array([iz-1,iz,iz+1]))].mean(axis=-1)
        X,Y=np.meshgrid(coords[i],coords[j],indexing='ij')
        weights=np.maximum(slab,0.)
        wsum=np.sum(weights)
        return [float(np.sum(X*weights)/wsum),float(np.sum(Y*weights)/wsum)] if wsum>1e-30 else [None,None]


def make_config(seed='T_2_3_B1600_N512',n=32,steps=3,dt=.003,box=BOXSIZE,sigma=SIGMA,gamma_bg=.05):
    return dict(seed=seed,n=int(n),steps=int(steps),dt=float(dt),box=float(box),sigma=float(sigma),gamma_bg=float(gamma_bg))


def campaign(config,output_dir,run_time=True):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    pts,path=source_points(config['seed']); bg=racetrack()
    g=EulerGrid(config['n'],config['box']);start=time.perf_counter()
    knot,kdiag=g.seed(pts,sigma=config['sigma'])
    back,bdiag=g.seed(bg,gamma=config['gamma_bg'],sigma=config['sigma'])
    L0=length(pts)
    cases={'free_knot':np.stack([knot]),'background_only':np.stack([back]),
           'coupled':np.stack([knot,back]),'frozen_background_diagnostic':np.stack([knot,back])}
    results={'config':config,'status':'DEVELOPMENT_ONLY_NO_EQUILIBRIUM_CERTIFICATION',
        'geometry':{'L0_source_polyline':L0,'source_n':len(pts),'background_n':len(bg),
           'source_sha256':source_hash(path),'trefoil_seed_diagnostics':kdiag,
           'background_seed_diagnostics':bdiag,'background_return_x':2.0,
           'background_height_half':1.3,
           'background_origin_branch':'x=y=0, -1.3<=z<=1.3',
           'model':'periodic cube, closed Gaussian-mollified polygon, both background legs live except diagnostic'},
        'case_results':{}}
    for name,state in cases.items():
        init=g.diagnostics(state,L0)
        record={'initial':init}
        if name in ('background_only','coupled','frozen_background_diagnostic'):
            record['bg_positive_z_centroid_initial']=g.centroid_bg(state[-1])
        if run_time and config['steps']>0:
            t=0.; initial_energy=init['energy'];initial_helicity=init['helicity']
            for step in range(config['steps']):
                vel=g.inv(g.velocity(np.sum(state,axis=0)))
                vmax=float(np.max(np.sqrt(np.sum(vel**2,axis=0))))
                cfl=vmax*config['dt']/g.dx
                if cfl>0.35: raise RuntimeError(f'CFL {cfl:.3g} > 0.35; reduce dt')
                state=g.rk4(state,config['dt'],name=='frozen_background_diagnostic')
                t+=config['dt']
            fin=g.diagnostics(state,L0)
            record.update({'final':fin,'time':t,
                'relative_energy_change':float((fin['energy']-initial_energy)/max(1e-30,abs(initial_energy))),
                'relative_helicity_change':float((fin['helicity']-initial_helicity)/max(1e-30,abs(initial_helicity)))})
            if name in ('background_only','coupled','frozen_background_diagnostic'):
                record['bg_positive_z_centroid_final']=g.centroid_bg(state[-1])
        results['case_results'][name]=record
    results['runtime_seconds']=time.perf_counter()-start
    # compare coupled minus independent baseline derivative at t=0: true cross effects
    a=results['case_results'];f=a['free_knot']['initial'];b=a['background_only']['initial'];c=a['coupled']['initial']
    # Quantify mutual induction in the actual initial fields; this explicitly
    # distinguishes potential (curl-free OUTSIDE support) velocity from vorticity.
    wk=g.inv(knot);wb=g.inv(back)
    u_k=g.inv(g.velocity(knot));u_b=g.inv(g.velocity(back))
    wK=np.sum(wk*wk,axis=0);wB=np.sum(wb*wb,axis=0)
    velB=np.sum(u_b*u_b,axis=0);velK=np.sum(u_k*u_k,axis=0)
    # Direct cross-advection RHS effects are computed in the same physical frame,
    # unlike separately fitted relative-equilibrium R* values (different fitted U).
    rhs_k_from_b=g.curl(g.fwd(np.cross(u_b,wk,axis=0)))
    rhs_b_from_k=g.curl(g.fwd(np.cross(u_k,wb,axis=0)))
    rms_cross=lambda v:float(np.sqrt(np.mean(np.sum(g.inv(v)**2,axis=0))))
    coupling={'rms_background_velocity_weighted_on_trefoil':float(np.sqrt(np.sum(wK*velB)/max(np.sum(wK),1e-30))),
      'rms_knot_velocity_weighted_on_background':float(np.sqrt(np.sum(wB*velK)/max(np.sum(wB),1e-30))),
      'vorticity_overlap_cauchy_ratio':float(np.sum(np.sqrt(wK*wB))/np.sqrt(max(np.sum(wK)*np.sum(wB),1e-30))),
      'direct_cross_rhs_knot_from_background_rms':rms_cross(rhs_k_from_b),
      'direct_cross_rhs_background_from_knot_rms':rms_cross(rhs_b_from_k)}
    if config['steps']>0 and run_time:
        pb=a['background_only']['bg_positive_z_centroid_final']
        pc=a['coupled']['bg_positive_z_centroid_final']
        if all(x is not None for x in (pb+pc)):
            coupling['background_deflection_coupled_minus_alone_xy']=[float(pc[i]-pb[i]) for i in range(2)]
    results['mutual_induction']=coupling
    results['comparison']={'knot_Rstar_free':f['component_residuals'][0]['R_star_L0'],
        'knot_Rstar_coupled':c['component_residuals'][0]['R_star_L0'],
        'background_Rstar_alone':b['component_residuals'][0]['R_star_L0'],
        'background_Rstar_coupled':c['component_residuals'][1]['R_star_L0'],
        'knot_Rstar_change':c['component_residuals'][0]['R_star_L0']-f['component_residuals'][0]['R_star_L0'],
        'background_Rstar_change':c['component_residuals'][1]['R_star_L0']-b['component_residuals'][0]['R_star_L0']}
    (out/(config['seed']+f'_n{config["n"]}.json')).write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
    return results


def main():
    parser=argparse.ArgumentParser(description='Fully coupled periodic Euler trefoil + single closed background racetrack pilot')
    parser.add_argument('--seed',choices=['T_2_3_B1600_N512','T_3_2_B1600_N512','both'],default='both')
    parser.add_argument('--n',type=int,default=32)
    parser.add_argument('--steps',type=int,default=3)
    parser.add_argument('--dt',type=float,default=.003)
    parser.add_argument('--sigma',type=float,default=SIGMA)
    parser.add_argument('--gamma-bg',type=float,default=.05)
    parser.add_argument('--out',default=str(ROOT/'Gate2_Coupled_Trefoil_Grid_v0.1.0-outputs'))
    args=parser.parse_args()
    for seed in (['T_2_3_B1600_N512','T_3_2_B1600_N512'] if args.seed=='both' else [args.seed]):
        cf=make_config(seed,args.n,args.steps,args.dt,sigma=args.sigma,gamma_bg=args.gamma_bg)
        r=campaign(cf,args.out)
        print(seed,'n=',args.n,'time=',r['runtime_seconds'],'R*_knot',r['comparison']['knot_Rstar_free'],'=>',r['comparison']['knot_Rstar_coupled'],'R*_bg',r['comparison']['background_Rstar_alone'],'=>',r['comparison']['background_Rstar_coupled'],flush=True)

if __name__=='__main__':main()
