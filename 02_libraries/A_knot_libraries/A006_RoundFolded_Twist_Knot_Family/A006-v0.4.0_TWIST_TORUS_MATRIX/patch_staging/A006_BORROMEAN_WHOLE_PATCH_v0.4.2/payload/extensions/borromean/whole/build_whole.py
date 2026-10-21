#!/usr/bin/env python3
"""A006 v0.4.2 — full-curve near-unknot component placement on reference Borromean forms.

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

def ref_lookup(ref,angles):
    c,u,v,normal,r,phase=circle_data(ref)
    a=np.unwrap(np.arctan2((ref-c)@v,(ref-c)@u))
    # Need a monotonically increasing periodic interpolant of phi -> xyz.
    da=np.diff(a)
    sign=1 if np.median(da)>0 else -1
    if np.min(sign*da)<-0.45:
        raise ValueError('Reference carrier not star-shaped in its fitted plane')
    # Enforce monotone interpolation for small backtracks from polygon coordinates.
    indices=np.argsort((sign*a)%(2*np.pi))
    x=(sign*a[indices])%(2*np.pi)
    px=ref[indices]
    valid=np.r_[True,np.diff(x)>1e-6]
    x=x[valid];px=px[valid]
    if len(x)<16:raise ValueError('Insufficient reference angular coverage')
    dest=((sign*angles)%(2*np.pi))
    coords=np.column_stack([np.interp(dest, np.r_[x,x[0]+2*np.pi], np.r_[px[:,k],px[0,k]]) for k in range(3)])
    return coords,c,u,v,normal,r

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

def kpc_text(name,branch):
    dest=f'output/borromean/{name}'
    base=['reset all','show backdrop','mode cb','bradius = 0.2','cradius = 0.1',
          'collision fast','energy model MD','mechforce = on','elecforce = on',
          f'tanforce = {"on" if branch=="ON" else "off"}','tanmag = 9',
          'stusplit = 0','dstep = 1','close = 0.20','max-dr = 0.02',
          f'load {dest}.xyz','information','lnknum','safe','length']
    if branch=='LOAD':return '\n'.join(base)+'\n'
    lines=base+[f'coords {dest}_{branch}_i00000.xyz']
    prev=0
    for n in (1,8,32,128,512):
        lines.extend((f'ago {n-prev}',f'echo WHOLE_{branch}_i{n:05d}',
                      'information','safe','lnknum','length',f'coords {dest}_{branch}_i{n:05d}.xyz'))
        prev=n
    lines.append('stop')
    return '\n'.join(lines)+'\n'

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--profiles',nargs='+',choices=list(CFG),default=['FLAT','SOFT','BALANCED','TIGHT'])
    ap.add_argument('--n',type=int,default=1024,choices=(1024,2048))
    ap.add_argument('--allow-unsafe',action='store_true',help='Do not use for dynamics; writes rejected candidates only for inspection')
    args=ap.parse_args()
    root=args.root.resolve()
    b=root/'output'/'borromean';b.mkdir(parents=True,exist_ok=True)
    # Preserve original source references; refuse silently overwriting user inputs.
    refdir=Path(__file__).resolve().parent/'references'
    for src in ('borromean_flat.txt','borromean_balanced.txt'):
        dest=b/src
        if dest.exists() and sha(dest)!=sha(refdir/src):
            raise RuntimeError('Reference conflict: '+str(dest))
        if not dest.exists():dest.write_bytes((refdir/src).read_bytes())
    from importlib.machinery import SourceFileLoader
    sys.path.insert(0,str(root/'extensions'/'borromean'))
    from build_borromean import locate_seed
    sources={}
    for knot in set(KNOTS):
        p,path=locate_seed(root,knot,args.n)
        sources[knot]=(p,str(path.relative_to(root)),sha(path))
    reports=[]
    for profile in args.profiles:
        name=f'Borromean_5_5_6_{profile}_N{args.n:04d}'
        refname,width,height=CFG[profile];ref=load_xyz(refdir/refname)
        if len(ref)!=3:raise RuntimeError('Invalid reference: not 3 components')
        comp=[];metadata=[]
        for i,knot in enumerate(KNOTS):
            # Keep each source WHOLE, never splice or replace subsections.
            Y,info=transport(sources[knot][0],ref[i],width,height)
            comp.append(Y);metadata.append(info)
        gaps=[clearance(x) for x in comp]
        inter=[clearance(comp[i],comp[j]) for i,j in PAIR]
        lk=[gauss(comp[i],comp[j]) for i,j in PAIR]
        finite=all(np.isfinite(x) for x in gaps+inter+lk)
        gates={'three_whole_components':'PASS','single_xyz_blank_separated':'PASS',
               'self_clearance':'PASS' if finite and min(gaps)>.20 else 'FAIL',
               'intercomponent_clearance':'PASS' if finite and min(inter)>.20 else 'FAIL',
               'pairwise_linking':'PASS' if finite and max(map(abs,lk))<.02 else 'FAIL',
               'component_knot_polynomials':'UNRESOLVED','Milnor_mu123':'UNRESOLVED',
               'whole_curve_isotopy':'UNRESOLVED','KnotPlot_runtime':'NOT_RUN','Euler':'NOT_RUN'}
        report={'release':'0.4.2','profile':profile,'reference_source':refname,
                'reference_sha256':sha(refdir/refname),'knot_types_intended':KNOTS,
                'n_per_component':args.n,'native_sources':{k:{'path':v[1],'sha256':v[2]} for k,v in sources.items()},
                'meta':metadata,'self_clearances':gaps,'intercomponent_clearances':inter,
                'pairwise_gauss_midpoint':lk,'gates':gates,
                'status':'DEVELOPMENT_STATIC_CANDIDATE' if all(gates[k]=='PASS' for k in ('self_clearance','intercomponent_clearance','pairwise_linking')) else 'STATIC_GEOMETRY_REJECTED',
                'topology_note':'Source winding around ring is zero: rigid transforms or tubular transport do not certify Borromean triple linking. Milnor mu123 must be measured independently.'}
        if report['status']!='DEVELOPMENT_STATIC_CANDIDATE' and not args.allow_unsafe:
            raise RuntimeError(f'Geometric gates reject {name}: {gates}; gaps={gaps}, inter={inter}, Lk={lk}. No loadable file written.')
        xyz=b/f'{name}.xyz'
        newtext='\n\n'.join('\n'.join('%.17g %.17g %.17g'%tuple(x) for x in p) for p in comp)+'\n'
        if xyz.exists():
            if xyz.read_text(encoding='ascii') != newtext:
                raise FileExistsError('Conflicting existing output, refusing overwrite: '+str(xyz))
            print('SKIP identical geometry:',name,flush=True)
            digest=sha(xyz)
        else:
            digest=write_xyz(xyz,comp)
        if len(load_xyz(xyz,args.n))!=3:raise RuntimeError('XYZ roundtrip')
        if report['status']=='DEVELOPMENT_STATIC_CANDIDATE':
            for branch in ('LOAD','ON','OFF'):
                text=kpc_text(name,branch)
                if branch=='LOAD':text=text.replace('tanforce = off','tanforce = off')
                suffix='LOAD' if branch=='LOAD' else 'TANF_'+branch+'_PILOT'
                (b/f'{name}_{suffix}.kpc').write_text(text,encoding='ascii')
        report['sha256_xyz']=digest
        (b/f'{name}_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        reports.append({'name':name,'status':report['status'],'self_min':min(gaps),'inter_min':min(inter),'linking':lk})
        print(name,report['status'],'self',round(min(gaps),3),'inter',round(min(inter),3),'lk',[round(x,4) for x in lk],flush=True)
    (b/'WHOLE_LATEST_BUILD.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
