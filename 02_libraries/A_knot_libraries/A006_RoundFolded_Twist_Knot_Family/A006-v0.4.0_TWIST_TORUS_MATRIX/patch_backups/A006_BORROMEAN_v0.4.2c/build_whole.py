#!/usr/bin/env python3
"""A006 v0.4.2b — full-curve near-unknot component placement on reference Borromean forms.

Each individual 5_2/6_1 curve is bent around an ENTIRE scaffold ring, without
cutting, splicing, or appending a knotblob. Static geometric candidates only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

KNOTS=('5_2','5_2','6_1')
PAIR=((0,1),(0,2),(1,2))
CFG={
 'FLAT':     ('borromean_flat.txt',0.37,0.72),
 'SOFT':     ('borromean_balanced.txt',0.27,0.65),
 'BALANCED': ('borromean_balanced.txt',0.40,0.85),
 'TIGHT':    ('borromean_balanced.txt',0.53,1.00),
}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_xyz(path,n=None):
    raw=Path(path).read_text(encoding='utf-8-sig')
    blocks=raw.strip().split('\n\n')
    comp=[]
    for b in blocks:
        if not b.strip():raise ValueError('Empty component')
        lines=b.splitlines()
        if any(not x.strip() for x in lines):raise ValueError('Multiple blank separators')
        p=np.asarray([[float(y) for y in x.split()] for x in lines],dtype=float)
        if p.ndim!=2 or p.shape[1]!=3 or len(p)<4 or not np.all(np.isfinite(p)):
            raise ValueError('Invalid XYZ component in '+str(path))
        if n is not None and len(p)!=n: raise ValueError(f'Wrong bead count {len(p)} expected {n}')
        comp.append(p)
    return comp

def write_xyz(path,comps):
    if len(comps)!=3:raise ValueError('Require exactly 3 components')
    text='\n\n'.join('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in p) for p in comps)+'\n'
    Path(path).write_text(text,encoding='ascii',newline='\n')
    return sha(path)

def circle_data(p):
    # Fit circle in principal plane; use a right-handed tangent-normal frame.
    center=p.mean(axis=0)
    _,_,v=np.linalg.svd(p-center,full_matrices=False)
    u=v[0];w=v[1];normal=np.cross(u,w)
    q=np.column_stack(((p-center)@u,(p-center)@w))
    A=np.column_stack((2*q[:,0],2*q[:,1],np.ones(len(q))))
    cx,cy,c0=np.linalg.lstsq(A,np.sum(q*q,axis=1),rcond=None)[0]
    c=center+cx*u+cy*w
    radius=np.linalg.norm(q-np.array([cx,cy]),axis=1)
    phase=np.arctan2(q[:,1]-cy,q[:,0]-cx)
    # All reference carriers must have degree ±1 around their fitted center.
    ph=np.unwrap(np.r_[phase,phase[0]])
    winding=round((ph[-1]-ph[0])/(2*np.pi))
    # Last point must account for wrapping by +/- 2pi, not as unwrapped same angle.
    delta=ph[-1]-ph[0]
    if abs(abs(delta)-2*np.pi)>.5:
        phase_un=np.unwrap(phase)
        drift=phase_un[-1]-phase_un[0]
        winding=1 if drift>0 else -1
        if abs(abs(drift)-2*np.pi)>.8:
            raise ValueError('Reference ring not angularly monotonic')
    else:phase_un=np.unwrap(phase)
    if np.sign(np.median(np.diff(phase_un)))<0:
        # reverse order in phase, values still correspond to original points
        pass
    return c,u,w,normal,float(np.mean(radius)),phase_un

def ref_lookup(ref, angles):
    """Correct periodic angular interpolation, including wrap BELOW first knot angle.

    Older v0.4.2a used np.interp with a missing left ghost vertex,
    clamping queries to the first reference point near 0/2pi and inducing
    nonphysical polygonal gaps.  This is a numerical fix, not an isotopy proof.
    """
    c,u,v,normal,r,_ = circle_data(ref)
    a=np.unwrap(np.arctan2((ref-c)@v,(ref-c)@u))
    da=np.diff(a)
    sign=1 if np.median(da)>0 else -1
    if np.min(sign*da)<-0.45:
        raise ValueError('Reference carrier not star-shaped in fitted plane')
    phi=(sign*a)%(2*np.pi)
    idx=np.argsort(phi); x=phi[idx];px=ref[idx]
    valid=np.r_[True,np.diff(x)>1e-6];x=x[valid];px=px[valid]
    if len(x)<16:raise ValueError('Reference resolution insufficient')
    # Periodic ghost knots on BOTH sides. No clamping and no jump at 2pi.
    xp=np.r_[x[-1]-2*np.pi, x, x[0]+2*np.pi]
    pp=np.vstack((px[-1],px,px[0]))
    dest=(sign*np.asarray(angles))%(2*np.pi)
    coords=np.column_stack([np.interp(dest,xp,pp[:,k]) for k in range(3)])
    return coords,c,u,v,normal,r


def polygon_length(p):
    return float(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1).sum())


def closed_resample(p,n):
    """Uniform arclength sampling of a cyclic polygon with NO duplicated end bead."""
    p=np.asarray(p,dtype=float)
    if len(p)<4 or n<32:raise ValueError('Need >= 32 beads and >=4 input vertices')
    seg=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    if not np.all(np.isfinite(seg)) or np.any(seg<=1e-10):
        raise ValueError('Source has duplicate/zero edge(s)')
    s=np.r_[0.,np.cumsum(seg)]
    targets=np.arange(n)*s[-1]/n
    x=np.vstack((p,p[0]))
    return np.column_stack([np.interp(targets,s,x[:,k]) for k in range(3)])


def edge_metrics(p):
    d=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    med=float(np.median(d))
    return {'length':float(d.sum()),'median_edge':med,
            'min_edge':float(d.min()),'max_edge':float(d.max()),
            'max_over_median':float(d.max()/med),
            'min_over_median':float(d.min()/med),
            'closure_edge':float(d[-1]),'closure_over_median':float(d[-1]/med)}


def allocate_counts(lengths, total=None, spacing=None, explicit=None):
    if explicit is not None:
        a=[int(x) for x in explicit]
    elif spacing is not None:
        if spacing<=0:raise ValueError('spacing > 0 required')
        a=[int(round(x/spacing)) for x in lengths]
    elif total is not None:
        if total<96:raise ValueError('total must exceed 96')
        q=np.array(lengths,dtype=float);q=q/q.sum()*total
        a=list(np.floor(q).astype(int))
        order=np.argsort(-(q-np.floor(q)))
        for i in order[:total-sum(a)]:a[i]+=1
    else:
        a=[1024]*3
    if len(a)!=3 or min(a)<32 or max(a)>65536:
        raise ValueError('Need three bead counts, each in [32,65536]')
    return tuple(int(v) for v in a)

def source_data(src):
    # Natural near-circle plane is XY by v0.4.0 seed construction.
    xy=src[:,:2]
    A=np.column_stack((2*xy[:,0],2*xy[:,1],np.ones(len(src))))
    cx,cy,_=np.linalg.lstsq(A,(xy*xy).sum(axis=1),rcond=None)[0]
    radius=np.hypot(xy[:,0]-cx,xy[:,1]-cy)
    phase=np.arctan2(xy[:,1]-cy,xy[:,0]-cx)
    winding=int(np.rint(np.sum((np.diff(np.unwrap(np.r_[phase,phase[0]]))))/(2*np.pi)))
    return phase,radius-radius.mean(),src[:,2]-src[:,2].mean(),radius.mean(),winding

def transport(source,reference,width_factor,height_factor,scale=60.0,phase_offset=0.0):
    phase,delta,z,r,winding=source_data(source)
    carrier,refcenter,u,v,normal,refR=ref_lookup(reference,phase+phase_offset)
    angle=phase+phase_offset
    radial=np.cos(angle)[:,None]*u +np.sin(angle)[:,None]*v
    # scales based on ratio of major radii, preserves relative thinness
    radial_amp=width_factor*refR/r
    vert_amp=height_factor*refR/r
    Y=carrier+radial_amp*delta[:,None]*radial+vert_amp*z[:,None]*normal
    return Y*scale, {'source_winding':winding,'scaffold_radius':refR,'radial_factor':radial_amp,
                     'normal_factor':vert_amp,'global_scale':scale,'phase_offset':phase_offset}

def gauss(a,b):
    A=np.roll(a,-1,axis=0)-a; B=np.roll(b,-1,axis=0)-b
    pa=(a+np.roll(a,-1,axis=0))*.5;pb=(b+np.roll(b,-1,axis=0))*.5
    res=0.
    for k in range(0,len(a),32):
        d=pa[k:k+32,None,:]-pb[None,:,:]
        dn=np.linalg.norm(d,axis=2)
        if dn.min()<1e-12:return float('nan')
        res+=np.sum(np.einsum('ijk,ijk->ij',np.cross(A[k:k+32,None,:],B[None,:,:]),d)/dn**3)
    return float(res/(4*np.pi))

def segment_dist(p0,p1,q0,q1):
    # Robust vectorized segment-to-segment shortest distance.
    u=p1-p0;v=q1-q0;w=p0-q0
    a=(u*u).sum(axis=1);b=(u*v).sum(axis=1);c=(v*v).sum(axis=1)
    d=(u*w).sum(axis=1);e=(v*w).sum(axis=1)
    den=a*c-b*b
    s=np.zeros(len(den)); mask=den>1e-12
    s[mask]=np.clip((b[mask]*e[mask]-c[mask]*d[mask])/den[mask],0,1)
    t=np.clip((b*s+e)/np.maximum(c,1e-30),0,1)
    s=np.clip((b*t-d)/np.maximum(a,1e-30),0,1)
    t=np.clip((b*s+e)/np.maximum(c,1e-30),0,1)
    return np.linalg.norm(w+s[:,None]*u-t[:,None]*v,axis=1)

def clearance(a,b=None,skip=8):
    same=b is None
    if same:b=a
    a1=np.roll(a,-1,axis=0);b1=np.roll(b,-1,axis=0)
    mids=(a+a1)/2; midb=(b+b1)/2
    r=np.linalg.norm(a-a1,axis=1)/2;rb=np.linalg.norm(b-b1,axis=1)/2
    tree=cKDTree(midb);best=float('inf')
    if same: radius=2.0 +r.max()+rb.max()
    else:
        nearest=np.min(tree.query(mids,k=1)[0]); radius=max(2.,nearest+r.max()+rb.max()+.05)
    for i,m in enumerate(mids):
        js=tree.query_ball_point(m,radius)
        if same:js=[j for j in js if min(abs(i-j),len(a)-abs(i-j))>skip]
        if not js:continue
        j=np.array(js,dtype=int)
        d=segment_dist(np.repeat(a[i:i+1],len(j),axis=0),np.repeat(a1[i:i+1],len(j),axis=0),b[j],b1[j])
        best=min(best,float(d.min()))
    return best if np.isfinite(best) else max(0.,radius-r.max()-rb.max())

def main():
    ap=argparse.ArgumentParser(description='A006 whole-component periodic seam fix, XYZ ONLY')
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--profiles',nargs='+',choices=list(CFG),default=['FLAT','SOFT','BALANCED','TIGHT'])
    g=ap.add_mutually_exclusive_group()
    g.add_argument('--n-per-component',type=int,nargs=3,metavar=('N0','N1','N2'))
    g.add_argument('--total-beads',type=int)
    g.add_argument('--target-spacing',type=float)
    g.add_argument('--n',type=int,help='legacy equal N for all 3 components')
    ap.add_argument('--source-n',type=int,choices=(1024,2048),default=2048)
    ap.add_argument('--allow-unsafe',action='store_true',help='write rejected geometry only for inspection, no physical qualification')
    args=ap.parse_args()
    root=args.root.resolve()
    b=root/'output'/'borromean';b.mkdir(parents=True,exist_ok=True)
    refdir=Path(__file__).resolve().parent/'references'
    for src in ('borromean_flat.txt','borromean_balanced.txt'):
        dest=b/src
        if dest.exists() and sha(dest)!=sha(refdir/src):raise RuntimeError('Reference conflict: '+str(dest))
        if not dest.exists():dest.write_bytes((refdir/src).read_bytes())
    sys.path.insert(0,str(root/'extensions'/'borromean'))
    from build_borromean import locate_seed
    sources={}
    for knot in set(KNOTS):
        p,path=locate_seed(root,knot,args.source_n)
        sources[knot]=(p,str(path.relative_to(root)),sha(path))
    results=[]
    for profile in args.profiles:
        refname,width,height=CFG[profile];refs=load_xyz(refdir/refname)
        if len(refs)!=3:raise RuntimeError('Reference must have 3 components')
        raw=[];meta=[]
        for i,knot in enumerate(KNOTS):
            Y,info=transport(sources[knot][0],refs[i],width,height)
            raw.append(Y);meta.append(info)
        pre_metrics=[edge_metrics(y) for y in raw]
        lengths=[polygon_length(y) for y in raw]
        requested=(args.n,)*3 if args.n else args.n_per_component
        counts=allocate_counts(lengths,total=args.total_beads,spacing=args.target_spacing,explicit=requested)
        comp=[closed_resample(y,n) for y,n in zip(raw,counts)]
        metrics=[edge_metrics(y) for y in comp]
        # Uniformity checks include last-to-first; do not equate adjacent endpoints.
        edge_ok=all((m['min_over_median']>0.55 and m['max_over_median']<1.35 and
                      0.65<m['closure_over_median']<1.35) for m in metrics)
        if not edge_ok:
            raise RuntimeError(f'Edge/seam gate FAIL for {profile}: {metrics}. No output written')
        gaps=[clearance(x,skip=max(8,int(len(x)/128))) for x in comp]
        inter=[clearance(comp[i],comp[j]) for i,j in PAIR]
        # Coarse linking check to keep FULL build affordable; not Milnor.
        lk=[gauss(comp[i][::max(1,len(comp[i])//512)],comp[j][::max(1,len(comp[j])//512)]) for i,j in PAIR]
        finite=all(np.isfinite(x) for x in gaps+inter+lk)
        gates={'three_whole_components':'PASS','numeric_xyz_only':'PASS',
               'periodic_reference_interpolation':'PASS',
               'cyclic_equal_arclength':'PASS' if edge_ok else 'FAIL',
               'self_clearance':'PASS' if finite and min(gaps)>.20 else 'FAIL',
               'intercomponent_clearance':'PASS' if finite and min(inter)>.20 else 'FAIL',
               'pairwise_linking':'PASS' if finite and max(map(abs,lk))<.02 else 'FAIL',
               'component_polynomials':'UNRESOLVED','Milnor_mu123':'UNRESOLVED',
               'KnotPlot_closed_flag':'NOT_RUN','KnotPlot_ago':'NOT_RUN','Euler':'NOT_RUN'}
        accepted=all(gates[k]=='PASS' for k in ('cyclic_equal_arclength','self_clearance','intercomponent_clearance','pairwise_linking'))
        label=('N%04d'%counts[0]) if len(set(counts))==1 else ('N%d_%d_%d'%counts)
        name=f'Borromean_5_5_6_{profile}_{label}_v042b'
        report={'release':'v0.4.2b','source_v0.4.0':{k:{'path':v[1],'sha256':v[2]} for k,v in sources.items()},
                'profile':profile,'component_knots_intended':KNOTS,'n_per_component':counts,
                'source_5_2_vs_6_1_length_ratio':polygon_length(sources['6_1'][0])/polygon_length(sources['5_2'][0]),
                'reference':refname,'reference_hash':sha(refdir/refname),
                'lengths_pre_resample':lengths,'metrics_pre_resample':pre_metrics,
                'metrics_after_resample':metrics,'self_clearance':gaps,'intercomponent_clearance':inter,
                'pairwise_linking_coarse':lk,'meta':meta,'gates':gates,
                'status':'STATIC_CANDIDATE' if accepted else 'REJECTED',
                'note':'Input remains three complete components, with no labels and exactly 2 blank separators. Closed polygon indexing is implicit; KnotPlot closed/open flag MUST be checked after user loads XYZ. Not a Milnor or isotopy certification.'}
        if not accepted and not args.allow_unsafe:
            raise RuntimeError(f'Geometric gates reject {name}: {gates}; no file written.')
        xyz=b/(name+'.xyz');reportpath=b/(name+'_REPORT.json')
        newtext='\n\n'.join('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in p) for p in comp)+'\n'
        if xyz.exists():
            if xyz.read_text('ascii')!=newtext:
                raise FileExistsError('Existing output differs, refuse overwrite: '+str(xyz))
            print('SKIP identical:',name)
        else:write_xyz(xyz,comp)
        from strict_xyz import assert_strict_xyz
        assert_strict_xyz(xyz,counts)
        report['sha256_xyz']=sha(xyz)
        if reportpath.exists():
            if json.loads(reportpath.read_text()).get('sha256_xyz')!=sha(xyz):
                raise FileExistsError('Conflicting report, refusing overwrite: '+str(reportpath))
        reportpath.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        results.append({'file':xyz.name,'counts':counts,'status':report['status'],
                        'lengths':[round(q['length'],5) for q in metrics],
                        'max_edge_ratio':[round(q['max_over_median'],4) for q in metrics]})
        print(name,report['status'],'counts',counts,'max_edge_ratio',results[-1]['max_edge_ratio'],flush=True)
    (b/'WHOLE_v042b_LATEST_BUILD.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
