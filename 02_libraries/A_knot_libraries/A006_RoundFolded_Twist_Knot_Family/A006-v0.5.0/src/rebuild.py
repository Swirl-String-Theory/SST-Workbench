#!/usr/bin/env python3
"""Rebuild geometric twist-knot seeds from exactly compiled TikZ Hobby centerlines.

Requires: pdflatex, pdftocairo, numpy, scipy, shapely, sympy, matplotlib.
No physical Euler or KnotPlot dynamics are executed. The assigned 3D crossings
are alternating; they are NOT a reverse engineering of TikZ flip crossing IDs.
"""
from __future__ import annotations
import hashlib, json, math, re, subprocess, sys, struct, argparse
from pathlib import Path
import numpy as np
from scipy.interpolate import CubicSpline
from shapely.geometry import LineString
from shapely.strtree import STRtree

ROOT=Path(__file__).resolve().parents[1]
LABS=['4_1','7_2','8_1','9_2','10_1','11a247']
CONTROLS=['6_1']  # 5_2 intentionally excluded: coincident P3/P10, non-minimal crossing projection
EXPECTED={'4_1':(4,5), '6_1':(6,9), '7_2':(7,11),'8_1':(8,13),'9_2':(9,15),'10_1':(10,17),'11a247':(11,19)}
RES=(256,512,1024,2048)
PROFILES={'TIKZ_NATIVE':1.0,'ROUND':.65}
SCALE_RADIUS=75.0
HEADER=b'KnotPlot 1.0\n\x0c\n'

def sha(b):return hashlib.sha256(b).hexdigest()
def savejson(path,datum):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(datum,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')

def compile_original_hobby(label):
    """Recover the actual vector Bezier segments from pdflatex; not Catmull-Rom substitution."""
    ref=ROOT/'REF_TIKZ'/f'{label}_original_reference.tex'
    txt=ref.read_text(encoding='utf8')
    coords=re.findall(r'\\coordinate\s+\(P(\d+)\)\s+at\s+\(([^)]*)\);',txt)
    assert len(coords)>=10 and [int(x[0]) for x in coords]==list(range(1,len(coords)+1)),label
    work=ROOT/'_tex_build'/label;work.mkdir(parents=True,exist_ok=True)
    coordinate_commands='\n'.join(f'\\coordinate (P{idx}) at ({xy});' for idx,xy in coords)
    latex=(r'\documentclass[tikz,border=1pt]{standalone}'+'\n'+r'\usepackage{tikz}'+'\n'+r'\usetikzlibrary{hobby}'+'\n'+r'\begin{document}'+'\n'+r'\begin{tikzpicture}[use Hobby shortcut]'+'\n'+coordinate_commands+'\n'+r'\draw[line width=.1pt] ([closed] P1)'+''.join(f'..(P{idx})' for idx,_ in coords[1:])+';\n'+r'\end{tikzpicture}'+'\n'+r'\end{document}'+'\n')
    (work/'path.tex').write_text(latex,encoding='utf8')
    run=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(work),str(work/'path.tex')],capture_output=True,timeout=30)
    if run.returncode:raise RuntimeError(f'pdflatex failed {label}: {run.stdout.decode(errors="replace")[-1500:]}')
    subprocess.run(['pdftocairo','-svg',str(work/'path.pdf'),str(work/'path.svg')],check=True,timeout=20)
    txt=(work/'path.svg').read_text(encoding='utf8')
    d=re.search(r'<path fill="none"[^>]+d="([^"]+)"',txt)
    if not d:raise ValueError('No stroked Hobby path in SVG')
    vectors=d.group(1).split(' Z ')[0].split(' Z')[0]
    vals=np.array([float(x) for x in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:e[-+]?\d+)?',vectors)])
    assert (len(vals)-2)%6==0
    start=vals[:2];last=start.copy();arr=[]
    for j in range((len(vals)-2)//6):
        b,c,d=vals[2+6*j:2+6*(j+1)].reshape(3,2)
        u=np.arange(140)/140
        points=((1-u)**3)[:,None]*last+3*((1-u)**2*u)[:,None]*b+3*((1-u)*u*u)[:,None]*c+(u**3)[:,None]*d
        arr.append(points);last=d
    pts=np.concatenate(arr)/28.346456692913385  # TikZ cm -> PostScript pt
    return pts, {'tex_file':str(ref.relative_to(ROOT)),'tex_sha256':sha(ref.read_bytes()),'control_points':len(coords),
                 'bezier_segments':(len(vals)-2)//6,'path_extraction':'pdflatex Hobby shortcut -> PDF vector -> SVG cubic Beziers, sampled',
                 'max_svg_start_end_gap_cm':float(np.linalg.norm(start-last)/28.346456692913385)}

def project_crossings(xy):
    n=len(xy)
    seg=[LineString([xy[i],xy[(i+1)%n]]) for i in range(n)]
    tree=STRtree(seg); crossing=[]
    for i,line in enumerate(seg):
        for jj in tree.query(line,predicate='intersects'):
            j=int(jj)
            if j<=i or min((j-i)%n,(i-j)%n)<=2:continue
            hit=line.intersection(seg[j])
            if hit.geom_type!='Point':raise ValueError(f'Non-point crossing {i}-{j}: {hit.geom_type}')
            a=xy[(i+1)%n]-xy[i]; b=xy[(j+1)%n]-xy[j]
            cross=float(np.linalg.det(np.array([a,b])))
            if abs(cross)<1e-11:raise ValueError('Tangent/degenerate crossing')
            q=np.array([hit.x,hit.y]); s=float(i+np.dot(q-xy[i],a)/np.dot(a,a));t=float(j+np.dot(q-xy[j],b)/np.dot(b,b))
            crossing.append({'s':s/n,'t':t/n,'signed_xy':int(np.sign(cross)),'intersection_xy':[float(x) for x in q]})
    return sorted(crossing,key=lambda x:x['s'])

def crossing_trace(cs):
    e=sorted([(c['s'],i,'a') for i,c in enumerate(cs)]+[(c['t'],i,'b') for i,c in enumerate(cs)])
    for i in range(len(cs)):
        seen=[k%2 for k,(_,j,_) in enumerate(e) if j==i]
        if sorted(seen)!=[0,1]:raise ValueError(f'Not an alternating diagram: crossing {i}: {seen}')
    return e

def fox_determinant(cs):
    e=crossing_trace(cs);n=len(cs)
    labels={};u=0
    for k,(_,j,_) in enumerate(e):
        typ='O' if k%2==0 else 'U'
        if typ=='U':u+=1
        labels[(j,typ)]=(u-1)%n
    mat=np.zeros((n,n),dtype=np.int64)
    for i in range(n):
        o=labels[(i,'O')];after=labels[(i,'U')];before=(after-1)%n
        mat[i,o]+=2;mat[i,before]-=1;mat[i,after]-=1
    return int(abs(round(np.linalg.det(mat[:-1,:-1]))))

def periodic_z(e,n,h=.18):
    ss=np.array([v[0] for v in e]); signs=np.array([1 if k%2==0 else -1 for k in range(len(e))]);
    assert np.all(np.diff(ss)>1e-12)
    f=CubicSpline(np.r_[ss,ss[0]+1],np.r_[signs,signs[0]]*h,bc_type='periodic')
    frac=np.arange(n)/n
    return f(np.where(frac<ss[0],frac+1,frac))

def roundfold(p,alpha):
    if alpha==1:return p.copy()
    out=p.copy();center=(np.max(p[:,:2],axis=0)+np.min(p[:,:2],axis=0))/2
    q=p[:,:2]-center;r=np.linalg.norm(q,axis=1)
    if r.min()<0.15:raise ValueError(f'Bad polar center; near axis: {r.min()}')
    R=float(np.median(r)); rr=R+alpha*(r-R)
    if rr.min()<=0:raise ValueError('Negative compressed radius')
    out[:,:2]=center+q*(rr/r)[:,None]
    return out

def arclength_resample(p,n):
    p=np.asarray(p,dtype=float);ed=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    assert ed.min()>1e-9
    s=np.r_[0,np.cumsum(ed)];u=np.arange(n)*s[-1]/n
    return np.column_stack([np.interp(u,s,np.r_[p[:,d],p[0,d]]) for d in range(3)])

def packkpt(p):
    xyz=np.asarray(p,dtype='>f8').tobytes()
    return HEADER+b'comp'+b'Attr'+struct.pack('>I',1)+b'LOCD'+struct.pack('>I',len(xyz))+xyz+b'endf'

def unpackkpt(data):
    assert data.startswith(HEADER)
    loc=data.index(b'LOCD',len(HEADER));length=struct.unpack('>I',data[loc+4:loc+8])[0]
    assert data[loc+8+length:]==b'endf'
    return np.frombuffer(data[loc+8:loc+8+length],dtype='>f8').reshape(-1,3).astype(float)

def local_clearance(p):
    # Globally exhaustive nonadjacent pairs for n <= 256, else accelerated certified midpoint-radius upper bound.
    from scipy.spatial import cKDTree
    n=len(p);seg=np.roll(p,-1,axis=0)-p;mid=p+seg/2; lens=np.linalg.norm(seg,axis=1);skip=4
    tree=cKDTree(mid); pairs=set();near=tree.query(mid,k=min(n,28))[1]
    for i, js in enumerate(near):
        for jj in np.atleast_1d(js):
            j=int(jj)
            if i<j and min(j-i,n-(j-i))>skip:pairs.add((i,j))
    if not pairs:raise ValueError('No nonlocal candidate')
    from scipy.spatial.distance import cdist
    def dsegment(i,j):
        p0=p[i];q0=p[j];u=seg[i];v=seg[j];w=p0-q0
        a=u@u;b=u@v;c=v@v;d=u@w;e=v@w;D=a*c-b*b
        sn=D;sd=D;tn=D;td=D
        if D<1e-16:sn=0;sd=1;tn=e;td=c
        else:
            sn=b*e-c*d;tn=a*e-b*d
            if sn<0:sn=0;tn=e;td=c
            elif sn>sd:sn=sd;tn=e+b;td=c
        if tn<0:
            tn=0
            if -d<0:sn=0
            elif -d>a:sn=sd
            else:sn=-d;sd=a
        elif tn>td:
            tn=td
            if (-d+b)<0:sn=0
            elif (-d+b)>a:sn=sd
            else:sn=-d+b;sd=a
        sc=0 if abs(sn)<1e-16 else sn/sd;tc=0 if abs(tn)<1e-16 else tn/td
        return float(np.linalg.norm(w+sc*u-tc*v))
    best=min(dsegment(i,j) for i,j in pairs)
    rad=best+lens.max()+1e-8
    for i in range(n):
        for jj in tree.query_ball_point(mid[i],rad):
            j=int(jj)
            if i>=j or min(j-i,n-(j-i))<=skip:continue
            v=dsegment(i,j)
            if v<best:best=v
    return float(best)

def metrics(p):
    e=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    a=p-np.roll(p,1,axis=0);b=np.roll(p,-1,axis=0)-p
    turns=np.arccos(np.clip(np.sum(a*b,axis=1)/(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)),-1,1))
    return {'mean_edge':float(e.mean()),'edge_cv':float(e.std()/e.mean()),
            'closure_edge_over_median':float(e[-1]/np.median(e)),
            'max_edge_over_median':float(e.max()/np.median(e)),
            'min_edge_over_median':float(e.min()/np.median(e)),
            'max_turn_degrees':float(np.rad2deg(turns.max())),
            'min_nonlocal_centerline_distance':local_clearance(p),
            'length':float(e.sum())}

def main():
    manifest={'release':'A006-v0.5.0f-TIKZ-SOURCE-REBUILD','status':'GEOMETRY_CANDIDATE_NOT_KNOTPLOT_RUNTIME_CERTIFIED',
       'physical_Euler':'NOT_RUN','knotplot_runtime':'NOT_RUN',
       'sources':{},'results':[], 'quarantine':[], 'controls':{},'notes':['All curves sampled from actual compiled TikZ Hobby vector Beziers.','Over/under assignment is independently alternating (not exact TikZ flip indices).','5_2 has 8 geometric intersections and coincident P3/P10; previous validated version retained as control.']}
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,4,figsize=(16,8),constrained_layout=True)
    for ii,name in enumerate(LABS+CONTROLS):
        dense2d,prov=compile_original_hobby(name);manifest['sources'][name]=prov
        cs=project_crossings(dense2d)
        expN,expDet=EXPECTED[name]
        det=fox_determinant(cs)
        assert len(cs)==expN and det==expDet,(name,len(cs),det,expN,expDet)
        e=crossing_trace(cs)
        dense=np.column_stack([dense2d,periodic_z(e,len(dense2d))])
        r0=np.median(np.linalg.norm(dense2d,axis=1));dense*=SCALE_RADIUS/r0
        ax=axes.flat[ii];ax.plot(dense[:,0],dense[:,1],lw=1.0,color='#005eae');ax.set_aspect('equal');ax.axis('off');ax.set_title(f'{name}: {expN} crossings, |Δ(-1)|={det}')
        for profile,alpha in PROFILES.items():
            d=roundfold(dense,alpha)
            for n in RES:
                x=arclength_resample(d,n)
                # derive mirror through coordinate reflection only
                for mirrored in (False,True):
                    y=x.copy()
                    if mirrored:y[:,0]*=-1
                    # Verify actual crossing count and invariant after sampling.
                    try:
                        pcs=project_crossings(y[:,:2]);cross_n=len(pcs);cd=fox_determinant(pcs)
                        m=metrics(y)
                        gate=(cross_n==expN and cd==expDet and m['edge_cv']<0.07 and
                              m['min_nonlocal_centerline_distance']>0.12 and m['max_edge_over_median']<1.35 and
                              m['closure_edge_over_median']<1.35 and m['max_turn_degrees']<22.0)
                        errors=[] if gate else ['ONE_OR_MORE_GEOMETRY_GATES_FAILED']
                    except Exception as ex:
                        cross_n=-1;cd=-1;m={};gate=False;errors=[str(ex)]
                    name_out=f'KNOT_{name}_N{n:04d}_{"MIRROR" if mirrored else "ORIG"}_{profile}'
                    base=ROOT/('SEEDS' if gate else 'QUARANTINE')
                    np.savetxt(base/(name_out+'.xyz'),y,fmt='%.17g')
                    kpt=packkpt(y)
                    assert np.array_equal(unpackkpt(kpt),y)
                    (base/(name_out+'.kpt')).write_bytes(kpt)
                    datum={'name':name,'source':'TIKZ_HOBBY','n':n,'profile':profile,'mirror':mirrored,
                           'target_crossings':expN,'actual_crossings':cross_n,'target_determinant':expDet,'actual_determinant':cd,
                           'status':'STATIC_CANDIDATE' if gate else 'QUARANTINE','geometry':m,'failure_reason':errors,
                           'xyz_sha256':sha((base/(name_out+'.xyz')).read_bytes()),'kpt_sha256':sha(kpt)}
                    savejson(base/(name_out+'.json'),datum)
                    manifest['results' if gate else 'quarantine'].append(datum)
        print(name, 'source crossings/det', expN,det,'created')
    axes.flat[7].axis('off')
    axes.flat[7].text(.1,.5,'TikZ-Hobby source projections\nNo 4-plat C-sector transformation\nStatic geometry only',fontsize=14,va='center')
    fig.suptitle('A006 v0.5.0f — exact compiled TikZ Hobby source projections',fontsize=14)
    fig.savefig(ROOT/'PREVIEWS'/'TIKZ_SOURCE_COMPARISON.png',dpi=180)
    plt.close(fig)
    savejson(ROOT/'MANIFEST.json',manifest)
    print('SUMMARY:',len(manifest['results']),'PASS',len(manifest['quarantine']),'quarantine')

if __name__=='__main__':main()
