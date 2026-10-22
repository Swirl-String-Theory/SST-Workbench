"""Additive Borromean decorated-link static candidate builder for RoundFolded v0.4.0.

No changes to existing geometry or runs. Dependencies: NumPy and SciPy. Source seeds
are ALWAYS read from the target release directory at BUILD time. Linking-zero alone
is NOT a certificate of Milnor triple linkage nor of component knot identity.
"""
import argparse, hashlib, json, math, struct
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

WORD=[(0,1),(1,-1)]*3
PAIR=((0,1),(0,2),(1,2))
PROFILE={"SOFT":{"height":24.,"size":30.,"bridge":40,"gap":8},
         "BALANCED":{"height":24.,"size":31.,"bridge":40,"gap":8},
         "TIGHT":{"height":24.,"size":32.,"bridge":40,"gap":8}}
HEADER=b'KnotPlot 1.0\n\x0c\n'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def encode(comps):
    chunks=[HEADER]
    for p in comps:
        b=np.asarray(p,dtype='>f8').tobytes()
        chunks.extend((b'comp',b'Attr',struct.pack('>I',1),b'LOCD',struct.pack('>I',len(b)),b))
    return b''.join(chunks+[b'endf'])
def decode(blob):
    if not blob.startswith(HEADER):raise ValueError('Not KnotPlot 1.0 KPT')
    i=len(HEADER);comps=[]
    while blob[i:i+4]!=b'endf':
        if blob[i:i+4]!=b'comp' or blob[i+4:i+8]!=b'Attr':raise ValueError('Malformed KPT component')
        i+=8
        if struct.unpack('>I',blob[i:i+4])[0]!=1:raise ValueError('Unsupported Attr')
        i+=4
        if blob[i:i+4]!=b'LOCD':raise ValueError('Unsupported LOC')
        i+=4
        n=struct.unpack('>I',blob[i:i+4])[0];i+=4
        if n%24 or i+n>len(blob):raise ValueError('Invalid KPT length')
        comps.append(np.frombuffer(blob[i:i+n],dtype='>f8').reshape(-1,3).astype(np.float64));i+=n
    if i+4!=len(blob):raise ValueError('Trailing KPT data')
    return comps

def locate_seed(root,knot,n):
    manifest=json.loads((root/'SEED_MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('version') != '0.4.0':
        raise RuntimeError('Native v0.4.0 SEED_MANIFEST.json required')
    name=f'{knot}_N{n}'
    candidates=[]
    for path in [root/'output'/'seeds'/f'{name}.kpt',root/'seeds'/f'{name}.kpt']:
        if path.is_file():candidates.append(path)
    if len(candidates)!=1:
        raise FileNotFoundError(f'Expected exactly one authoritative {name}.kpt in output/seeds/ or seeds/; found {candidates}. No fallback to arbitrary external data.')
    entries=[s for s in manifest['seeds'] if s['name']==knot and s['n']==n]
    if len(entries)!=1 or entries[0]['source_sha256']!=sha(candidates[0]):
        raise RuntimeError(f'Native v0.4.0 manifest SHA mismatch: {name}')
    p=decode(candidates[0].read_bytes())
    if len(p)!=1 or len(p[0])!=n or not np.isfinite(p[0]).all():raise ValueError('Invalid native seed: '+str(candidates[0]))
    return p[0],candidates[0]

def skeleton(n_event=128,R=100.,beta=15.,amp=8.):
    at=np.arange(3); strands=[[] for _ in range(3)]
    for k,(slot,sgn) in enumerate(WORD):
        for m in range(n_event):
            u=m/n_event;h=.5*(1-np.cos(np.pi*u));theta=2*np.pi*(k+u)/len(WORD)
            for c in range(3):
                j=int(at[c]);lane=float(j-1);z=0.
                if j==slot:lane+=h;z=sgn*amp*np.sin(np.pi*u)**2
                elif j==slot+1:lane-=h;z=-sgn*amp*np.sin(np.pi*u)**2
                rad=R+beta*lane
                strands[c].append((rad*np.cos(theta),rad*np.sin(theta),z))
        for c in range(3):
            if at[c]==slot:at[c]=slot+1
            elif at[c]==slot+1:at[c]=slot
    if not np.array_equal(at,np.arange(3)):raise RuntimeError('Braid closure mismatch')
    return [np.array(s,dtype=float) for s in strands]

def sample_closed(q,n):
    edge=np.roll(q,-1,axis=0)-q;L=np.linalg.norm(edge,axis=1)
    if L.min()<1.e-9:raise ValueError('Nonpositive edge')
    c=np.r_[0.,L.cumsum()]; t=np.arange(n)*c[-1]/n; j=np.searchsorted(c,t,side='right')-1
    return q[j]+((t-c[j])/L[j])[:,None]*edge[j]

def unit(x):
    r=np.linalg.norm(x)
    if r<1e-12:raise ValueError('Zero tangent')
    return x/r

def lift_knot(source,center,tangent,size,height):
    s=source-source.mean(axis=0)
    s=s*(size/np.max(np.linalg.norm(s,axis=1)))
    # Choose exposed low-z edge as source cut. Preserve original cyclic bead order.
    cut=int(np.argmin(s[:,2]+np.roll(s,-1,axis=0)[:,2]));next_=(cut+1)%len(s)
    dt=s[next_]-s[cut]
    a=math.atan2(tangent[1],tangent[0])-math.atan2(dt[1],dt[0]);c=math.cos(a);d=math.sin(a)
    rot=np.array([[c,-d,0],[d,c,0],[0,0,1]])
    s=s@rot.T; midpoint=(s[cut]+s[next_])/2
    s=s+center+np.array([0.,0.,height])-midpoint
    order=[(next_+j)%len(s) for j in range(len(s))]
    return s[order],cut

def bridge(A,B,tA,tB,num):
    dist=np.linalg.norm(B-A); u=(np.arange(1,num+1)/(num+1))[:,None]
    mA=unit(tA)*min(.45*dist,2.6);mB=unit(tB)*min(.45*dist,2.6)
    return (2*u**3-3*u**2+1)*A+(-2*u**3+3*u**2)*B+(u**3-2*u**2+u)*mA+(u**3-u**2)*mB

def decorate(carrier,src,event,n_event,cfg):
    n=len(carrier);k=event*n_event;gap=cfg['gap']
    left=(k-gap)%n;right=(k+gap)%n
    remain=np.array([carrier[(right+i)%n] for i in range((left-right)%n+1)])
    A=remain[-1];B=remain[0]
    # Keep all grafting near a single braid arc; explicit line geometry is later qualified.
    donor,edge=lift_knot(src,(A+B)/2,B-A,cfg['size'],cfg['height'])
    donor=donor[::-1]
    arm1=bridge(A,donor[0],A-remain[-2],donor[1]-donor[0],cfg['bridge'])
    arm2=bridge(donor[-1],B,donor[-1]-donor[-2],remain[1]-B,cfg['bridge'])
    return np.vstack([remain,arm1,donor,arm2]),{'donor_cut_edge':edge,'join_left':A.tolist(),'join_right':B.tolist()}

def gauss(a,b):
    A=np.roll(a,-1,axis=0)-a;B=np.roll(b,-1,axis=0)-b
    pa=(a+np.roll(a,-1,axis=0))*.5;pb=(b+np.roll(b,-1,axis=0))*.5
    total=0.
    for i in range(0,len(a),40):
        d=pa[i:i+40,None,:]-pb[None,:,:]
        denominator=np.linalg.norm(d,axis=2)**3
        if np.any(denominator<1.e-21):return float('nan')
        total+=np.sum(np.einsum('ijk,ijk->ij',np.cross(A[i:i+40,None,:],B[None,:,:]),d)/denominator)
    return float(total/(4*np.pi))

def dist_segment(P,P1,Q,Q1):
    # Vectorized exact min distance for n independent segment pairs.
    u=P1-P;v=Q1-Q;w=P-Q
    a=np.einsum('ij,ij->i',u,u);b=np.einsum('ij,ij->i',u,v);c=np.einsum('ij,ij->i',v,v)
    d=np.einsum('ij,ij->i',u,w);e=np.einsum('ij,ij->i',v,w)
    det=a*c-b*b;ss=np.zeros(len(Q))
    good=det>1e-15
    ss[good]=np.clip((b[good]*e[good]-c[good]*d[good])/det[good],0,1)
    tt=np.clip((b*ss+e)/np.maximum(c,1e-20),0,1)
    ss=np.clip((b*tt-d)/np.maximum(a,1e-20),0,1)
    tt=np.clip((b*ss+e)/np.maximum(c,1e-20),0,1)
    return np.linalg.norm(w+u*ss[:,None]-v*tt[:,None],axis=1)

def clearance(a,b=None,skip=5):
    if b is None:b=a;selfmode=True
    else:selfmode=False
    ca=(a+np.roll(a,-1,axis=0))*.5;cb=(b+np.roll(b,-1,axis=0))*.5
    ra=np.linalg.norm(a-np.roll(a,-1,axis=0),axis=1)*.5
    rb=np.linalg.norm(b-np.roll(b,-1,axis=0),axis=1)*.5
    tree=cKDTree(cb);best=float('inf')
    radius=3.5 + float(ra.max()+rb.max())
    if not selfmode:
        nearest=float(np.min(tree.query(ca,k=1)[0]))
        radius=max(radius,nearest+float(ra.max()+rb.max())+0.1)
    for i,mid in enumerate(ca):
        js=tree.query_ball_point(mid,radius)
        if selfmode:js=[j for j in js if min(abs(i-j),len(a)-abs(i-j))>skip]
        if not js:continue
        j=np.array(js,dtype=int)
        d=dist_segment(np.repeat(a[i:i+1],len(j),axis=0),np.repeat(a[(i+1)%len(a)][None,:],len(j),axis=0),b[j],b[(j+1)%len(b)])
        best=min(best,float(d.min()))
    if not np.isfinite(best):
        # No non-neighbour midpoint pairs within radius. Segment distance is
        # rigorously bounded below by radius - maximum edge half-lengths.
        return max(0.,radius-float(ra.max()+rb.max()))
    return float(best)

def geometry(root,profile,n,run_static=True):
    src=[];sources=[]
    for name in ('5_2','6_1'):
        p,file=locate_seed(root,name,n);src.append(p);sources.append({'name':name,'path':str(file.relative_to(root)),'sha256':sha(file)})
    sk=skeleton(n_event=max(64,n//8))
    comps=[];grafts=[]
    for i,(s,ev) in enumerate(zip((src[0],src[0],src[1]),(1,3,5))):
        q,meta=decorate(sk[i],s,ev,max(64,n//8),PROFILE[profile]);q=sample_closed(q,n)
        comps.append(q);grafts.append(meta)
    blob=encode(comps);decoded=decode(blob)
    if not all(np.array_equal(x,y) for x,y in zip(decoded,comps)):raise RuntimeError('KPT roundtrip failed')
    link=[gauss(comps[i],comps[j]) for i,j in PAIR]
    selfgap=[clearance(a) for a in comps]
    intergap=[clearance(comps[i],comps[j]) for i,j in PAIR]
    gates={'kpt_roundtrip':'PASS','pairwise_linking':('PASS' if all(np.isfinite(link)) and max(map(abs,link))<.02 else 'FAIL'),
          'self_clearance':('PASS' if np.isfinite(selfgap).all() and min(selfgap)>.20 else 'FAIL'),
          'intercomponent_clearance':('PASS' if np.isfinite(intergap).all() and min(intergap)>.20 else 'FAIL'),
          'component_polynomial':'UNRESOLVED','milnor_triple':'UNRESOLVED','continuous_splice_isotopy':'UNRESOLVED',
          'knotplot_ago':'NOT_RUN','Euler':'NOT_RUN'}
    return comps,blob,{'profile':profile,'n_per_component':n,'source':sources,'grafts':grafts,'base_version':'0.4.0','patch_version':'0.4.1',
            'pairwise_gauss_linking':link,'nonlocal_self_gap':selfgap,'intercomponent_gap':intergap,
            'gates':gates,'status':'DEVELOPMENT_STATIC_CANDIDATE',
            'note':'Circular smooth-graft prototype only: visual roundness and Milnor triple link NOT certified.'}

def write_kpc(out,name,profile,n,branch='OFF'):
    p=f'output/borromean_55261/{name}/{name}.kpt'
    tag='ON' if branch=='ON' else 'OFF'
    dest=f'output/borromean_55261/{name}/TANF_{tag}'
    cmd=['reset all','show backdrop','mode cb','bradius = 0.2','cradius = 0.1',
         'collision fast','energy model MD','mechforce = on','elecforce = on',
         'tanforce = '+('on' if tag=='ON' else 'off'), 'tanmag = 9',
         'stusplit = 0','dstep = 1','close = 0.20','max-dr = 0.02',
         'load '+p,'information','safe','lnknum','length',
         f'coords {dest}/i00000.xyz']
    last=0
    for iter in (1,8,32,128,512):
        cmd += [f'ago {iter-last}',f'echo BORROMEAN {profile} N{n} TANF {tag} checkpoint {iter}',
                'safe','lnknum','length',f'coords {dest}/i{iter:05d}.xyz',f'save {dest}/i{iter:05d}.k float']
        last=iter
    cmd.append('stop')
    (out/f'{name}_TANF_{tag}_PILOT.kpc').write_text('\n'.join(cmd)+'\n',encoding='ascii')

def build(root,profiles,n_list):
    results=[]
    for pr in profiles:
      for n in n_list:
        name=f'Borromean_5_2_5_2_6_1_{pr}_N{n:04d}'
        comps,blob,report=geometry(root,pr,n)
        # FAIL CLOSED: never publish failed geometry as a loadable KPT.
        if any(report['gates'][k]!='PASS' for k in
               ('kpt_roundtrip','pairwise_linking','self_clearance','intercomponent_clearance')):
            raise RuntimeError(f'Static geometry rejected before writing {name}: {report["gates"]}')
        dest=root/'output'/'borromean_55261'/name
        if dest.exists():
            raise FileExistsError(f'Refusing to overwrite generated folder: {dest}')
        dest.mkdir(parents=True,exist_ok=False)
        (dest/(name+'.kpt')).write_bytes(blob)
        for i,q in enumerate(comps):np.savetxt(dest/f'{name}_component{i}.xyz',q,fmt='%.17g')
        for branch in ('ON','OFF'):
            (dest/f'TANF_{branch}').mkdir(exist_ok=True)
            write_kpc(dest,name,pr,n,branch)
        report['sha256_kpt']=sha(dest/(name+'.kpt'))
        (dest/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
        results.append({'name':name,'gates':report['gates']})
        print(name,report['gates'],flush=True)
    (root/'output'/'borromean_55261'/'LATEST_BUILD.json').write_text(json.dumps(results,indent=2)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True)
    ap.add_argument('--profiles',nargs='+',choices=list(PROFILE),default=list(PROFILE))
    ap.add_argument('--n',nargs='+',type=int,default=[1024])
    x=ap.parse_args()
    build(x.root.resolve(),x.profiles,x.n)
if __name__=='__main__':main()
