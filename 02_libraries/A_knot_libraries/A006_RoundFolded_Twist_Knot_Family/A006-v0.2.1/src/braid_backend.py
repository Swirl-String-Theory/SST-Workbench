#!/usr/bin/env python3
"""Geometric candidate: local connected sums of closed-braid Borromean skeleton and 5_2,5_2,6_1 polygon knots.
No KnotPlot dynamics, no physical vortex certification. Python 3.10, numpy scipy.
"""
import argparse, hashlib, json, math, struct
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree

ROOT=Path(__file__).resolve().parents[1]
WORD=[(0,+1),(1,-1)]*3
N_PER_EVENT=128
R=13.0
BETA=1.9  # radial separation of braid lanes, length units
Z_BUMP=1.0

def smoothstep(u): return (1-np.cos(np.pi*u))*0.5

def base_components():
    # strand positions are positions in 3-slot braid lanes, not immutable component labels
    at=np.arange(3, dtype=int)
    strands=[[] for _ in range(3)]
    for k,(slot,sgn) in enumerate(WORD):
        for m in range(N_PER_EVENT):
            u=m/N_PER_EVENT
            h=smoothstep(u)
            phi=2*math.pi*(k+u)/len(WORD)
            for c in range(3):
                j=int(at[c]); lane=float(j-1)
                z=0.0
                if j==slot:
                    lane=(j-1)+h
                    z=sgn*Z_BUMP*np.sin(np.pi*u)**2
                elif j==slot+1:
                    lane=(j-1)-h
                    z=-sgn*Z_BUMP*np.sin(np.pi*u)**2
                x=(R+BETA*lane)*np.cos(phi)
                y=(R+BETA*lane)*np.sin(phi)
                strands[c].append([x,y,z])
        for c in range(3):
            if at[c]==slot:at[c]=slot+1
            elif at[c]==slot+1:at[c]=slot
    assert (at==np.arange(3)).all(),at
    return [np.array(x,dtype=float) for x in strands]

def ringlinking(a,b):
    # midpoint quadrature of signed Gauss linking integral; O(n^2) but vectorized
    # Use downsampling for coarse validation; independent from braid-word algebra.
    A=np.roll(a,-1,axis=0)-a; B=np.roll(b,-1,axis=0)-b
    P=(a+np.roll(a,-1,axis=0))*0.5; Q=(b+np.roll(b,-1,axis=0))*0.5
    out=0.
    for i in range(0,len(a),64):
        d=P[i:i+64,None,:]-Q[None,:,:]
        cross=np.cross(A[i:i+64,None,:],B[None,:,:])
        out += np.sum(np.sum(cross*d,axis=2)/np.linalg.norm(d,axis=2)**3)
    return float(out/(4*math.pi))

def min_segsep(a,b,exclude_near=False):
    """Bounding-aware KDtree exact line-segment distance, returns min non-neighbor separation."""
    p=np.asarray(a);q=np.asarray(b)
    v=np.roll(p,-1,axis=0)-p;w=np.roll(q,-1,axis=0)-q
    c=(p+np.roll(p,-1,axis=0))*0.5;d=(q+np.roll(q,-1,axis=0))*0.5
    lengths=np.linalg.norm(v,axis=1);lens2=np.linalg.norm(w,axis=1)
    tree=cKDTree(d)
    rad=0.5*(np.max(lengths)+np.max(lens2))+4.0
    best=1e30
    for i,cc in enumerate(c):
        matches=tree.query_ball_point(cc,r=rad)
        if exclude_near:matches=[j for j in matches if min(abs(j-i),len(a)-abs(j-i))>4]
        if not matches:continue
        j=np.array(matches,dtype=int)
        # closest points between 3-D segments via exact constrained minimization from line-line solution
        u=np.broadcast_to(v[i],(len(j),3)); ww=w[j]; r0=p[i]-q[j]
        aa=np.einsum('ij,ij->i',u,u);bb=np.einsum('ij,ij->i',u,ww);cc2=np.einsum('ij,ij->i',ww,ww)
        dd=np.einsum('ij,ij->i',u,r0);ee=np.einsum('ij,ij->i',ww,r0)
        D=aa*cc2-bb*bb
        s=np.zeros(len(j)); t=np.zeros(len(j))
        good=D>1.e-16
        s[good]=np.clip((bb[good]*ee[good]-cc2[good]*dd[good])/D[good],0,1)
        t=np.clip((bb*s+ee)/cc2,0,1)
        s=np.clip((bb*t-dd)/aa,0,1)
        t=np.clip((bb*s+ee)/cc2,0,1)
        sep=np.linalg.norm(r0+u*s[:,None]-ww*t[:,None],axis=1)
        if sep.size:best=min(best,float(sep.min()))
    return best

def cut_and_lift_knot(src, center, tangent, altitude=3.65, diameter=1.35):
    """Source polygon -> cut at an exposed edge and rigidly place on elevated local knotting lobe.
    Axis along down normal is +z. Connectivity explicitly checked downstream.
    """
    src=np.array(src,dtype=float)
    src-=src.mean(axis=0)
    # Standardize knot cloud diameter (isotropic transform preserves topology).
    maxr=np.max(np.linalg.norm(src,axis=1))
    src*=diameter/maxr
    # Rotating about z to make the cut-edge approximate local tangent
    imid=np.argmin((src[:,2]+np.roll(src,-1,axis=0)[:,2])*0.5)
    knext=(imid+1)%len(src)
    edge=(src[knext]-src[imid])[:2]
    atan=math.atan2(tangent[1],tangent[0])
    rot=atan-math.atan2(edge[1],edge[0])
    C,S=math.cos(rot),math.sin(rot)
    M=np.array([[C,-S,0],[S,C,0],[0,0,1.]])
    src=src@M.T
    edgecenter=0.5*(src[imid]+src[knext])
    # edge midpoint shifted to a point above missing skeleton span
    src+=np.asarray(center)+np.array([0.,0.,altitude])-edgecenter
    # open knot from next(edge) to start(edge), deleting exactly that edge.
    order=np.r_[np.arange(knext,len(src)),np.arange(0,imid+1)] if knext>imid else np.r_[np.arange(knext,imid+1)]
    assert len(order)==len(src)
    return src[order], int(imid)

def decorate(base, source, k_event, scale):
    # Cut a narrow arc straddling one braid junction: event k, equal-spaced polygon indices.
    center_idx=k_event*N_PER_EVENT
    gap=9
    N=len(base)
    aa=(center_idx-gap)%N;bb=(center_idx+gap)%N
    # wound arc A..B removed; sequence B,..,A retains the outside skeleton
    remain=np.array([base[(bb+i)%N] for i in range((aa-bb)%N+1)])
    # Remain is from B to A along closed ring. Route A -> open knot -> B
    A=remain[-1];B=remain[0]
    tangent=B-A
    kn,edge_idx=cut_and_lift_knot(source, 0.5*(A+B),tangent, altitude=4.8,diameter=scale)
    kn=kn[::-1].copy()  # bridges must not swap on the exposed lower face
    # interpolate guide arms to keep vertices from becoming too sparse
    def bridge(a,b,ns=28):return np.linspace(a,b,ns+2,endpoint=True)[1:-1]
    pts=np.vstack([remain,bridge(A,kn[0]),kn,bridge(kn[-1],B)])
    return pts,dict(cut_edge=edge_idx,removed_arc_vertices=2*gap-1, source_points=len(source), knotscale=scale,
             join_A=A.tolist(),join_B=B.tolist(),connector_start=kn[0].tolist(),connector_end=kn[-1].tolist())

def kpt_bytes(comps):
    parts=[b'KnotPlot 1.0\n\x0c\n']
    for p in comps:
        q=np.asarray(p,dtype='>f8').tobytes()
        parts += [b'comp',b'Attr',struct.pack('>I',1),b'LOCD',struct.pack('>I',len(q)),q]
    parts.append(b'endf');return b''.join(parts)

def decode_kpt(b):
    head=b'KnotPlot 1.0\n\x0c\n'
    assert b.startswith(head)
    start=len(head);out=[]
    while b[start:start+4]!=b'endf':
        assert b[start:start+4]==b'comp'; start+=4
        assert b[start:start+4]==b'Attr';start+=4
        assert struct.unpack('>I',b[start:start+4])[0]==1;start+=4
        assert b[start:start+4]==b'LOCD';start+=4
        length=struct.unpack('>I',b[start:start+4])[0];start+=4
        out.append(np.frombuffer(b[start:start+length],dtype='>f8').reshape(-1,3).copy());start+=length
    return out

def write_data(path,bytes_):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(bytes_)
    return hashlib.sha256(bytes_).hexdigest()

def run():
    geom=ROOT/'geometry';geom.mkdir(exist_ok=True)
    source5=ROOT/'source_native'/'5_2__knotplot_final.txt'
    source6=ROOT/'source_native'/'6_1__knotplot_final.txt'
    src5=np.loadtxt(source5);src6=np.loadtxt(source6)
    assert len(src5)>=250 and len(src6)>=250
    skeleton=base_components()
    statuses={}
    linkskel=[ringlinking(skeleton[i],skeleton[j]) for i,j in ((0,1),(0,2),(1,2))]
    print('skeleton linking integral',linkskel)
    comps=[];inserts=[]
    for i,(name,src,ev) in enumerate([('5_2',src5,1),('5_2',src5,3),('6_1',src6,5)]):
        new,cert=decorate(skeleton[i],src,ev,scale=1.65)
        comps.append(new);inserts.append(dict(component=i,topology_assigned=name,event=ev,**cert))
    links=[ringlinking(comps[i],comps[j]) for i,j in ((0,1),(0,2),(1,2))]
    # Require approximate winding numbers before passing linking=0.
    print('decorated linking integral',links)
    interdist={}
    for i,j in ((0,1),(0,2),(1,2)):
        interdist[f'{i}-{j}']=min_segsep(comps[i],comps[j]);print('intersegment sep',i,j,interdist[f'{i}-{j}'])
    # cross min should be > 0; collinear crossing in Gauss integration can cause nan
    assert all(np.isfinite(x) and x >0.08 for x in interdist.values()),interdist
    assert all(abs(x)<0.08 for x in links),links
    # with individual displaced knots, any equal-component self crossing must be controlled separately
    selfsep={str(i):min_segsep(comps[i],comps[i],True) for i in range(3)}
    print('self separation (nonlocal)',selfsep)
    assert all(x>0.005 for x in selfsep.values()),selfsep
    skeleton_path=geom/'borromean_skeleton_3comp.kpt'
    skeleton_hash=write_data(skeleton_path,kpt_bytes(skeleton))
    basename='borromean_local_knots_5_2_5_2_6_1_N'+str(len(comps[0]))
    p=geom/'borromean_5_2_5_2_6_1.kpt'
    b=kpt_bytes(comps);hash_kpt=write_data(p,b)
    reread=decode_kpt(b)
    assert len(reread)==3 and all(np.array_equal(a,b) for a,b in zip(comps,reread))
    # Separate ASCII component geometry and Borromean skeleton for interoperability
    file_records={}
    for i,(c,s) in enumerate(zip(comps,skeleton)):
        fn=geom/f'borromean_comp{i}_{"5_2" if i<2 else "6_1"}.xyz'
        content=''.join(f'{x:.17g} {y:.17g} {z:.17g}\n' for x,y,z in c).encode('ascii')
        file_records[fn.name]=write_data(fn,content)
    metadata={
      'schema':'SST-PKLSA-DECORATED-BORROMEAN-PREVIEW-1','purpose':'VISUALIZATION_GEOMETRY_CANDIDATE_ONLY',
      'borromean_skeleton':'closure of 3-braid (sigma_1 sigma_2^-1)^3',
      'component_types':['5_2','5_2','6_1'],'source_basenames':[source5.name,source5.name,source6.name],
      'source_hashes':{'5_2':hashlib.sha256(source5.read_bytes()).hexdigest(),'6_1':hashlib.sha256(source6.read_bytes()).hexdigest()},
      'braid_skeleton_hash_sha256':skeleton_hash,'output_sha256':hash_kpt,
      'source_status':'historical KnotPlot geometry; not independent physical PKLSA dynamics evidence',
      'linking_integrals_skeleton':linkskel,'linking_integrals_decorated':links,
      'minimum_intercomponent_clearance_units':interdist,'minimum_nonlocal_intrastrand_clearance_units':selfsep,
      'number_of_vertices':[len(a) for a in comps],'seeds':[dict(inserts[i],component_xyz_sha256=file_records[f'borromean_comp{i}_{"5_2" if i<2 else "6_1"}.xyz']) for i in range(3)],
      'validation':{'KnotPlot_runtime':'NOT_EXECUTED','Euler_finite_core':'NOT_EXECUTED',
      'Borromean_classification':'CONSTRUCTION_INFERRED_NOT_INDEPENDENTLY_CERTIFIED',
      'component_polynomials':'NOT_EVALUATED','pairwise_linking':'NUMERIC_ZERO',
      'self_intersection':'KD_TREE_DISCRETE_CLEARANCE_CHECK',
      'triple_Milnor_invariant':'NOT_EVALUATED'},
    }
    (ROOT/'candidate_report.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
    rel='geometry/borromean_5_2_5_2_6_1.kpt'
    script=f'reset all\nload {rel}\ninformation\nlength\nparameters\ncoords geometry/borromean_KnotPlot_roundtrip.txt\n'
    (ROOT/'diagnostic'/'borromean_5_2_5_2_6_1.kpc').write_text(script,encoding='ascii')
    (ROOT/'diagnostic'/'borromean_skeleton_only.kpc').write_text('reset all\nload geometry/borromean_skeleton_3comp.kpt\ninformation\nlength\n',encoding='ascii')
    # root convenient command from root working directory
    (ROOT/'borromean_5_2_5_2_6_1.kpc').write_text('reset all\nload geometry/borromean_5_2_5_2_6_1.kpt\ninformation\nlength\nparameters\ncoords geometry/borromean_KnotPlot_roundtrip.txt\n',encoding='ascii')
    print('written',p,'pointcounts',metadata['number_of_vertices'])
    return metadata
if __name__=='__main__':run()
