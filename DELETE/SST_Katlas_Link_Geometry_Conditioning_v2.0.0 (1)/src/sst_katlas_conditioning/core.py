from __future__ import annotations
from pathlib import Path
import json, math, re, shutil
import numpy as np
import networkx as nx

FORMAT = "SST-KATLAS-LINK-CONDITIONING-2.0"
TRANSLATOR_RAW = "SST-KATLAS-PD-3D-1.0"
CONDITIONER = "SST-KATLAS-ISOTOPY-HARMONIC-2.0"


def parse_katlas_pd(raw: str):
    if not raw: return None
    toks=re.findall(r'X\s*<sub>(.*?)</sub>',str(raw),re.I|re.S)
    if not toks: toks=re.findall(r'X\s*[\[(]([^]\)]*)[]\)]',str(raw),re.I|re.S)
    c=len(toks)
    if c<1: return None
    maxlab=2*c; options=[]
    for tok in toks:
        clean=re.sub(r'<[^>]+>','',tok).strip()
        if ',' in clean:
            vals=[int(x) for x in re.findall(r'\d+',clean)]
            options.append([tuple(vals)] if len(vals)==4 and all(1<=x<=maxlab for x in vals) else [])
            continue
        digits=re.sub(r'\D','',clean); opts=[]
        def rec(pos,parts):
            if len(parts)==4:
                if pos==len(digits): opts.append(tuple(parts))
                return
            rem=4-len(parts)
            for width in (1,2):
                if pos+width>len(digits): continue
                left=len(digits)-(pos+width)
                if left<rem-1 or left>2*(rem-1): continue
                ss=digits[pos:pos+width]
                if not ss or ss[0]=='0': continue
                v=int(ss)
                if 1<=v<=maxlab: rec(pos+width,parts+[v])
        rec(0,[]); options.append(opts)
    if any(not x for x in options): return None
    counts={i:0 for i in range(1,maxlab+1)}; chosen=[]; solution=None
    def bt(k):
        nonlocal solution
        if solution is not None: return
        if k==c:
            if all(v==2 for v in counts.values()): solution=list(chosen)
            return
        for op in options[k]:
            if any(counts[e]>=2 for e in op): continue
            for e in op: counts[e]+=1
            chosen.append(op); bt(k+1); chosen.pop()
            for e in op: counts[e]-=1
    bt(0); return solution


def gauss_component_count(raw: str):
    if not raw: return None
    groups=re.findall(r'\{[^{}]*\}',str(raw)); return len(groups) if groups else 1


def pd_to_components(pd, samples_per_segment=12):
    pd=[tuple(map(int,x)) for x in pd]; c=len(pd); inc={}
    for ci,t in enumerate(pd):
        if len(t)!=4: raise ValueError('PD crossing must have four edge labels')
        for e in t: inc.setdefault(e,[]).append(ci)
    if set(inc)!=set(range(1,2*c+1)) or any(len(v)!=2 for v in inc.values()): raise ValueError('invalid PD edge incidence')
    # Use canonical integer node ids. NetworkX's triangulation/layout internals may
    # iterate sets; tuple nodes containing strings are affected by Python hash
    # randomization across processes. Integer hashes are stable, making the raw
    # PD embedding deterministic for a fixed record and config.
    cnode=lambda ci: int(ci)
    enode=lambda e: int(c + e - 1)
    data={}
    for ci,t in enumerate(pd): data[cnode(ci)]=[enode(e) for e in reversed(t)]
    for e,cs in sorted(inc.items()): data[enode(e)]=[cnode(q) for q in cs]
    emb=nx.PlanarEmbedding(); emb.set_data(data); emb.check_structure(); pos=nx.combinatorial_embedding_to_pos(emb,fully_triangulate=False)
    xy={k:np.asarray(v,float) for k,v in pos.items()}; dists=[]
    for ci,t in enumerate(pd):
        C=xy[cnode(ci)]
        for e in t: dists.append(float(np.linalg.norm(xy[enode(e)]-C)))
    med=max(float(np.median(dists)),1e-6); radius=.18*med; lift=.25*med
    endpoints={}; pair={}; is_over={}
    for ci,(i,j,k,l) in enumerate(pd):
        pair[(ci,i)]=k; pair[(ci,k)]=i; pair[(ci,j)]=l; pair[(ci,l)]=j
        for e in (i,k): is_over[(ci,e)]=False
        for e in (j,l): is_over[(ci,e)]=True
        C=xy[cnode(ci)]
        for e in (i,j,k,l):
            d=xy[enode(e)]-C; d=d/(np.linalg.norm(d)+1e-15)
            endpoints[(ci,e)]=np.r_[C+radius*d, lift if is_over[(ci,e)] else -lift]
    other={}
    for e,(a,b) in inc.items(): other[(a,e)]=b; other[(b,e)]=a
    spp=max(6,int(samples_per_segment)); comps=[]; visited_edges=set()
    for start in sorted(inc):
        if start in visited_edges: continue
        c0=inc[start][0]; ci=c0; ein=start; chunks=[]; guard=0
        while True:
            guard+=1
            if guard>4*len(inc)+8: raise ValueError('PD component traversal did not close')
            visited_edges.add(ein); eout=pair[(ci,ein)]; z=lift if is_over[(ci,ein)] else -lift
            a=endpoints[(ci,ein)]; b=endpoints[(ci,eout)]; C=np.r_[xy[cnode(ci)],z]; u=np.linspace(0,1,spp,endpoint=False)[:,None]
            chunks.append((1-u)**2*a+2*(1-u)*u*C+u**2*b)
            cj=other[(ci,eout)]; b2=endpoints[(cj,eout)]; M=np.r_[xy[enode(eout)],0.0]
            chunks.append((1-u)**2*b+2*(1-u)*u*M+u**2*b2); ci=cj; ein=eout
            if ci==c0 and ein==start: break
        q=np.vstack(chunks); keep=np.ones(len(q),dtype=bool); keep[1:]=np.linalg.norm(np.diff(q,axis=0),axis=1)>1e-12; q=q[keep]
        if len(q)<8: raise ValueError('degenerate PD component')
        comps.append(q)
    return comps


def resample_closed(q,n):
    q=np.asarray(q,float); nxt=np.roll(q,-1,axis=0); seg=np.linalg.norm(nxt-q,axis=1); L=float(seg.sum())
    if L<=1e-15: raise ValueError('zero-length component')
    s=np.r_[0,np.cumsum(seg)]; qq=np.vstack([q,q[0]]); targets=np.linspace(0,L,int(n)+1)[:-1]
    out=np.empty((len(targets),3),float)
    j=0
    for i,t in enumerate(targets):
        while j+1<len(s)-1 and s[j+1]<=t: j+=1
        a=(t-s[j])/max(s[j+1]-s[j],1e-15); out[i]=(1-a)*qq[j]+a*qq[j+1]
    return out


def normalize_global(comps):
    arr=np.vstack(comps); c=arr.mean(axis=0); comps=[q-c for q in comps]; arr=np.vstack(comps); rg=float(np.sqrt(np.mean(np.sum(arr*arr,axis=1))))
    rg=max(rg,1e-15); return [q/rg for q in comps], {'center':c.tolist(),'rg_before':rg}


def fourier_truncate(q,h):
    q=np.asarray(q,float); n=len(q); F=np.fft.fft(q,axis=0); keep=np.zeros(n,bool); keep[0]=True
    h=min(int(h),(n-1)//2)
    for k in range(1,h+1): keep[k]=True; keep[-k]=True
    F[~keep]=0; return np.fft.ifft(F,axis=0).real


def circularize_first_harmonic(q):
    q=np.asarray(q,float); n=len(q); th=2*np.pi*np.arange(n)/n; C=q.mean(axis=0)
    A=(2.0/n)*np.sum((q-C)*np.cos(th)[:,None],axis=0); B=(2.0/n)*np.sum((q-C)*np.sin(th)[:,None],axis=0)
    na=np.linalg.norm(A)
    if na<1e-12: return q.copy()
    u=A/na; bp=B-u*np.dot(B,u); nb=np.linalg.norm(bp)
    if nb<1e-12: return q.copy()
    v=bp/nb; r=math.sqrt(max((na*na+nb*nb)/2.0,1e-15))
    return C+r*(np.cos(th)[:,None]*u+np.sin(th)[:,None]*v)


def tangent_angle_metrics(comps):
    vals=[]
    for q in comps:
        d=np.roll(q,-1,axis=0)-q; d=d/np.maximum(np.linalg.norm(d,axis=1)[:,None],1e-15); cc=np.sum(d*np.roll(d,-1,axis=0),axis=1); vals.extend(np.arccos(np.clip(cc,-1,1)).tolist())
    a=np.asarray(vals,float); return {'turn_angle_max_rad':float(a.max(initial=0)),'turn_angle_rms_rad':float(np.sqrt(np.mean(a*a))) if len(a) else 0.0}


def arclength_cv(comps):
    vals=[]
    for q in comps: vals.extend(np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1).tolist())
    a=np.asarray(vals,float); return float(a.std()/max(a.mean(),1e-15))


def densify(q,n): return resample_closed(q,max(int(n),len(q)))


def numerical_clearance(comps, guard_points=192, neighbor_skip=3):
    dc=[densify(q,guard_points) for q in comps]; best=np.inf
    for i,a in enumerate(dc):
        # self clearance, exclude local circular neighbors
        D=np.linalg.norm(a[:,None,:]-a[None,:,:],axis=2); m=len(a); idx=np.arange(m); sep=np.abs(idx[:,None]-idx[None,:]); sep=np.minimum(sep,m-sep); D[sep<=neighbor_skip]=np.inf; best=min(best,float(np.min(D)))
        for j in range(i+1,len(dc)):
            b=dc[j]; d=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2); best=min(best,float(np.min(d)))
    return float(best)


def gauss_linking_number(a,b):
    # midpoint quadrature of the Gauss integral; sufficient as an independent signature guard
    a=np.asarray(a,float); b=np.asarray(b,float); da=np.roll(a,-1,axis=0)-a; db=np.roll(b,-1,axis=0)-b; ma=.5*(a+np.roll(a,-1,axis=0)); mb=.5*(b+np.roll(b,-1,axis=0))
    r=ma[:,None,:]-mb[None,:,:]; den=np.maximum(np.linalg.norm(r,axis=2)**3,1e-15); cross=np.cross(da[:,None,:],db[None,:,:]); num=np.sum(cross*r,axis=2); return float(np.sum(num/den)/(4*np.pi))


def linking_matrix(comps):
    n=len(comps); M=np.zeros((n,n),float)
    for i in range(n):
        for j in range(i+1,n): M[i,j]=M[j,i]=gauss_linking_number(comps[i],comps[j])
    return M


def linking_signature_matches(a,b,tol=0.22):
    A=linking_matrix(a); B=linking_matrix(b)
    return bool(A.shape==B.shape and np.array_equal(np.rint(A).astype(int),np.rint(B).astype(int)) and np.max(np.abs(A-B),initial=0)<=float(tol)),A,B


def homotopy_clearance(raw,cand,lambdas=11,guard_points=128):
    if len(raw)!=len(cand): return 0.0
    best=np.inf
    for lam in np.linspace(0,1,int(lambdas)):
        comps=[(1-lam)*a+lam*b for a,b in zip(raw,cand)]
        best=min(best,numerical_clearance(comps,guard_points=guard_points))
    return float(best)


def condition_components(raw_comps,cfg):
    n=int(cfg.get('n_points_per_component',96)); raw=[resample_closed(q,n) for q in raw_comps]; raw,_=normalize_global(raw)
    raw=[resample_closed(q,n) for q in raw]; raw_metrics={**tangent_angle_metrics(raw),'ds_cv':arclength_cv(raw),'clearance':numerical_clearance(raw,int(cfg.get('guard_points',128)))}
    maxh=int(cfg.get('max_harmonics',12)); minclear=float(cfg.get('min_homotopy_clearance',0.025)); lk_tol=float(cfg.get('linking_number_tolerance',0.22)); trials=[]; accepted=None
    for h in range(1,maxh+1):
        cand=[fourier_truncate(q,h) for q in raw]
        if h==1 and bool(cfg.get('circularize_first_harmonic',True)): cand=[circularize_first_harmonic(q) for q in cand]
        cand=[resample_closed(q,n) for q in cand]
        hclear=homotopy_clearance(raw,cand,int(cfg.get('homotopy_samples',11)),int(cfg.get('guard_points',128)))
        lkok,A,B=linking_signature_matches(raw,cand,lk_tol)
        met={**tangent_angle_metrics(cand),'ds_cv':arclength_cv(cand),'clearance':numerical_clearance(cand,int(cfg.get('guard_points',128)))}
        curvature_improved=met['turn_angle_rms_rad'] <= raw_metrics['turn_angle_rms_rad']*float(cfg.get('max_curvature_rms_ratio',0.90))
        ok=bool(hclear>=minclear and lkok and curvature_improved)
        trials.append({'harmonics':h,'accepted':ok,'homotopy_min_clearance':hclear,'linking_signature_ok':lkok,'raw_linking_matrix':A.tolist(),'conditioned_linking_matrix':B.tolist(),**met})
        if ok: accepted=(h,cand,met,hclear,A,B); break
    if accepted is None:
        return raw, {'format':FORMAT,'conditioner':CONDITIONER,'status':'FALLBACK_RAW_UNIFORM','accepted':False,'selected_harmonics':None,'raw_metrics':raw_metrics,'trials':trials}
    h,cand,met,hclear,A,B=accepted
    return cand, {'format':FORMAT,'conditioner':CONDITIONER,'status':'CONDITIONED_TOPOLOGY_GUARDED','accepted':True,'selected_harmonics':h,'raw_metrics':raw_metrics,'conditioned_metrics':met,'homotopy_min_clearance':hclear,'raw_linking_matrix':A.tolist(),'conditioned_linking_matrix':B.tolist(),'trials':trials}


def load_katlas_link(path: Path):
    obj=json.loads(Path(path).read_text(encoding='utf-8',errors='ignore')); ident=obj.get('identity',{}) or {}
    if str(ident.get('kind','')).lower()!='link': raise ValueError('not a Katlas link record')
    pres=obj.get('presentations',{}) or {}; raw_pd=next((x for x in (pres.get('pd') or []) if str(x).strip()),None); pd=parse_katlas_pd(raw_pd)
    if not pd: raise ValueError('no supported PD presentation')
    comps=pd_to_components(pd); raw_gauss=next((x for x in (pres.get('gauss') or []) if str(x).strip()),None); expected=gauss_component_count(raw_gauss)
    if expected is not None and len(comps)!=expected: raise ValueError(f'component mismatch PD={len(comps)} Gauss={expected}')
    return obj,pd,comps


def save_conditioned(record_path: Path,out_dir: Path,cfg):
    obj,pd,raw=load_katlas_link(record_path); comps,report=condition_components(raw,cfg); out_dir=Path(out_dir); out_dir.mkdir(parents=True,exist_ok=True)
    offsets=[0]; arr=[]
    for q in comps: arr.append(q); offsets.append(offsets[-1]+len(q))
    np.savez_compressed(out_dir/'conditioned_geometry.npz',points=np.vstack(arr),component_offsets=np.asarray(offsets,dtype=np.int64))
    shutil.copy2(record_path,out_dir/'katlas.json')
    ident=obj.get('identity',{}) or {}; report.update({'katlas_id':ident.get('katlas_id',record_path.parent.name),'source_record':str(record_path),'n_components':len(comps),'pd_crossings':[list(x) for x in pd],'geometry_origin':'generated_from_katlas_pd_conditioned','source_coordinates':False,'raw_translator':TRANSLATOR_RAW})
    (out_dir/'conditioning.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    for i,q in enumerate(comps,1): np.savetxt(out_dir/f'component_{i:02d}.xyz',q,fmt='%.12g')
    return report


def relative_output_dir(root: Path, record: Path, out_root: Path):
    try: rel=record.parent.relative_to(root)
    except ValueError: rel=Path(record.parent.name)
    return out_root/rel


def scan_links(root: Path):
    rows=[]; root=Path(root)
    for p in sorted(root.rglob('katlas.json')):
        try:
            obj=json.loads(p.read_text(encoding='utf-8',errors='ignore')); ident=obj.get('identity',{}) or {}
            if str(ident.get('kind','')).lower()!='link': continue
            pres=obj.get('presentations',{}) or {}; raw_pd=next((x for x in (pres.get('pd') or []) if str(x).strip()),None); pd=parse_katlas_pd(raw_pd) if raw_pd else None
            rows.append({'path':str(p),'katlas_id':ident.get('katlas_id',p.parent.name),'pd_ok':bool(pd),'crossings':ident.get('crossings')})
        except Exception as e: rows.append({'path':str(p),'katlas_id':p.parent.name,'pd_ok':False,'error':repr(e)})
    return rows
