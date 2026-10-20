#!/usr/bin/env python3
"""RoundFolded twist-knot geometry candidates, not certified topology or Euler solutions.

Topological FAMILY: Conway [m,2], T_m. Geometric realization: splice a provenance-
tracked representative into a circular or closed-braid carrier using two smooth bridges.
Not a proof of ambient isotopy; topological gates remain unresolved unless certified.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

from braid_backend import kpt_bytes, decode_kpt, min_segsep, ringlinking, base_components, cut_and_lift_knot
import braid_backend as b

ROOT=Path(__file__).resolve().parents[1]
NAMES={1:'3_1',2:'4_1',3:'5_2',4:'6_1',5:'7_2',6:'8_1'}
NAMES.update({7:'9_2',8:'10_1'})


def uniformize(p, labels, n_target):
    """Closed arclength remesh plus origin-region tags; original source remains untouched."""
    ds=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    if np.min(ds)<=1.e-12: raise ValueError('Degenerate input edge')
    arclen=np.r_[0.,np.cumsum(ds)]
    positions=np.arange(n_target)*arclen[-1]/n_target
    idx=np.minimum(np.searchsorted(arclen,positions,side='right')-1,len(p)-1)
    return p[idx]+((positions-arclen[idx])/ds[idx])[:,None]*(np.roll(p,-1,axis=0)-p)[idx], np.asarray(labels)[idx]


def unit(x):
    d=np.linalg.norm(x)
    if d<=1.e-12: raise ValueError('Zero tangent vector')
    return x/d


def resample_closed(p,n):
    p=np.asarray(p,dtype=np.float64)
    edge=np.roll(p,-1,axis=0)-p
    ds=np.linalg.norm(edge,axis=1)
    if len(p)<10 or np.min(ds)<1e-10: raise ValueError('Input not valid closed polygon')
    cumulative=np.r_[0.,np.cumsum(ds)]
    tgt=np.arange(n)*cumulative[-1]/n
    idx=np.minimum(np.searchsorted(cumulative,tgt,side='right')-1,len(p)-1)
    return p[idx]+((tgt-cumulative[idx])/ds[idx])[:,None]*edge[idx]


def bridge(A,B,ta,tb,n):
    # C1 Hermite curve with endpoint tangents; *no* claim of safe isotopy.
    da=np.linalg.norm(B-A)
    d=min(0.4*da,0.75)
    a=d*unit(ta); z=d*unit(tb)
    u=(np.arange(1,n+1)/(n+1))[:,None]
    return ((2*u**3-3*u**2+1)*A+(-2*u**3+3*u**2)*B
           +(u**3-2*u**2+u)*a+(u**3-u**2)*z)


def circle(n,radius):
    t=np.arange(n)*2*np.pi/n
    return np.column_stack((radius*np.cos(t),radius*np.sin(t),np.zeros(n)))


def decorate(carrier,src,at,source_diameter=1.80,knot_offset=1.12,
             fold_ratio=0.80,nbridge=20,ngap=7,bridge_bulge=0.55):
    """One local connected-sum *candidate* with near-circular carrier and compact knot.

    Source is isotropically scaled by cut_and_lift_knot; an invertible transverse
    contraction is then applied. Long bridges are explicit and recorded for auditing.
    """
    carrier=np.asarray(carrier,dtype=np.float64)
    src=np.asarray(src,dtype=np.float64)
    n=len(carrier); ix=at%n
    ai=(ix-ngap)%n; bi=(ix+ngap)%n
    rem=np.array([carrier[(bi+i)%n] for i in range((ai-bi)%n+1)])
    A=rem[-1]; B=rem[0]; tangent=unit(B-A)
    # local knot near the carrier, not far above it
    knot,edge=cut_and_lift_knot(src,0.5*(A+B),B-A,
                                altitude=knot_offset,diameter=source_diameter)
    knot=knot[::-1].copy()
    # invertible affine transverse squeeze keeps topology of the knot summand
    centroid=knot.mean(axis=0)
    rel=knot-centroid
    knot=centroid+rel*fold_ratio+(1-fold_ratio)*np.outer(rel@tangent,tangent)
    # Tangent-correct Hermite bridges, with no smoothing applied to source knot.
    a=bridge(A,knot[0],A-rem[-2],knot[1]-knot[0],nbridge)
    c=bridge(knot[-1],B,knot[-1]-knot[-2],rem[1]-B,nbridge)
    # Give the two returning branches distinct smooth radial shoulders.
    # The common near-contact at the two branch endpoints remains auditable.
    radial=unit(np.array([(A[0]+B[0])/2,(A[1]+B[1])/2,0.0]))
    uu=np.arange(1,nbridge+1)/(nbridge+1)
    a+=bridge_bulge*np.sin(np.pi*uu)[:,None]**2*radial
    c-=bridge_bulge*np.sin(np.pi*uu)[:,None]**2*radial
    poly=np.vstack([rem,a,knot,c])
    region=np.array(['carrier']*len(rem)+['bridge']*len(a)
                     +['knot']*len(knot)+['bridge']*len(c))
    return poly,region,{'source_cut_edge':int(edge),'carrier_cut_a':int(ai),
              'carrier_cut_b':int(bi),'knot_scale_diameter':source_diameter,
              'fold_ratio':fold_ratio,'knot_offset':knot_offset}


def stats(p):
    seg=np.roll(p,-1,axis=0)-p
    ds=np.linalg.norm(seg,axis=1)
    c=np.sum(seg*np.roll(seg,1,axis=0),axis=1)/(ds*np.roll(ds,1))
    turns=np.rad2deg(np.arccos(np.clip(c,-1,1)))
    return {'n':len(p),'length':float(ds.sum()),'edge_min':float(ds.min()),
            'edge_median':float(np.median(ds)), 'edge_max':float(ds.max()),
            'edge_ratio':float(ds.max()/ds.min()),'max_turn_degrees':float(turns.max()),
            'min_nonlocal_self_segment_distance':float(min_segsep(p,p,True))}


def emit(case,geoms,regions,records,provenance,kind):
    out=ROOT/'output'/kind/case
    out.mkdir(parents=True,exist_ok=True)
    bdata=kpt_bytes(geoms)
    assert all(np.array_equal(x,y) for x,y in zip(geoms,decode_kpt(bdata)))
    gc=[ringlinking(geoms[i],geoms[j]) for i,j in [(0,1),(0,2),(1,2)]] if len(geoms)==3 else []
    clearance={f'{i}-{j}':float(min_segsep(geoms[i],geoms[j])) for i,j in [(0,1),(0,2),(1,2)]} if len(geoms)==3 else {}
    report={'version':'0.1.0','status':'STATIC_TOPOLOGY_UNCERTIFIED',
      'scientific_scope':'KnotPlot geometric seed, not Euler/PKLSA velocity/vorticity field',
      'case':case,'component_count':len(geoms),'components':records,
      'sha256_kpt':hashlib.sha256(bdata).hexdigest(),
      'provider_files_sha256':provenance,
      'pairwise_gauss_linking_numerical':gc,
      'intercomponent_clearances':clearance,
      'gates':{'source_bytes_present':'PASS','kpt_roundtrip':'PASS',
               'knot_polynomial_and_isotopy':'UNRESOLVED',
               'triple_Milnor_mu123':'UNRESOLVED' if len(geoms)==3 else 'NOT_APPLICABLE',
               'KnotPlot_GO':'NOT_TESTED','finite_core_Euler':'NOT_TESTED'}}
    if any(v<0.12 for v in clearance.values()): raise ValueError(f'{case}: component crossing or contact')
    if any(rec['geometry']['min_nonlocal_self_segment_distance']<0.12 for rec in records):
        raise ValueError(f'{case}: zero nonlocal self clearance')
    kpt=out/(case+'.kpt');kpt.write_bytes(bdata)
    for i,(geo,labels) in enumerate(zip(geoms,regions)):
        np.savetxt(out/f'component_{i}.xyz',geo,fmt='%.17g')
        (out/f'component_{i}_region.csv').write_text('bead_index,region\n'+''.join(f'{j},{r}\n' for j,r in enumerate(labels)),encoding='utf-8')
    relat=kpt.relative_to(ROOT).as_posix()
    (out/(case+'_LOAD.kpc')).write_text('reset all\nload '+relat+'\ninformation\nlength\n',encoding='ascii')
    (out/(case+'_GO1.kpc')).write_text('reset all\nload '+relat+'\ncollision fast\ninformation\ngo 1\n',encoding='ascii')
    (out/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def load_source(m,custom_sources=None):
    custom_sources=custom_sources or {}
    name=NAMES.get(m,f'Tm{m}')
    path=Path(custom_sources[m]) if m in custom_sources else ROOT/'source_native'/f'{name}.xyz'
    if not path.exists():
        raise FileNotFoundError(f'No source for m={m}, expected {path}. '
              f'Run KnotPlot acquisition/acquire_Tm{m}.kpc then supply source XYZ.')
    arr=np.loadtxt(path,ndmin=2)
    if arr.shape[1]!=3:raise ValueError(f'{path}: expected 3 columns')
    return arr,hashlib.sha256(path.read_bytes()).hexdigest(),name


def build_individual(m,points=512,scale=7.0,radius=11.0,fold=0.8):
    src,sha,name=load_source(m)
    # Source resampling does not itself certify isotopy, record in report.
    if len(src)!=points: src=resample_closed(src,points)
    car=circle(max(320,int(points*0.78)),radius)
    g,region,meta=decorate(car,src,at=0,source_diameter=1.85,fold_ratio=fold,
                            knot_offset=1.2,nbridge=24,ngap=8)
    g,region=uniformize(g,region,max(512,points*2))
    g*=scale
    info={'label':name,'m':m,'Conway':f'[{m},2]','anticipated_determinant':2*m+1,
           'sampling':points,'source_sha256':sha,'metadata':meta,'geometry':stats(g)}
    return emit(f'Tm{m}_{name}_N{points:04d}',[g],[region],[info],{name:sha},'individual')


def build_borromean(ms=(3,3,4),n=256,scale=7.0,fold=0.8):
    # Closed 3-braid (sigma1 sigma2^-1)^3 yields Borromean skeleton; a topological
    # proof of the *decorated* resulting triple is a separate required gate.
    b.N_PER_EVENT=max(32,int(n/5));b.R=11.;b.BETA=1.9
    sk=b.base_components()
    curves=[];regions=[];records=[];sha={}
    for i,(m,event) in enumerate(zip(ms,(1,3,5))):
        src,s,name=load_source(m)
        if len(src)!=n:src=resample_closed(src,n)
        p,region,meta=decorate(sk[i],src,at=event*b.N_PER_EVENT,
            source_diameter=1.60,knot_offset=1.55,
            fold_ratio=fold,nbridge=20,ngap=5)
        p,region=uniformize(p,region,max(768,3*n))
        p*=scale
        curves.append(p);regions.append(region)
        sha[name]=s
        records.append({'label':name,'m':m,'anticipated_determinant':2*m+1,
                        'source_sha256':s,'metadata':meta,'geometry':stats(p)})
    case='Borromean_'+'_'.join(NAMES.get(x,f'Tm{x}') for x in ms)+f'_N{n:04d}'
    return emit(case,curves,regions,records,sha,'borromean')


def acquire():
    out=ROOT/'acquisition';out.mkdir(exist_ok=True)
    for m in range(1,13):
        name=NAMES.get(m,f'Tm{m}')
        txt=f'''% KnotPlot Conway rational-tangle construction; must inspect output and classify topology.\nreset all\nconway {m}2\ninformation\ncoords source_native/{name}.xyz\n'''
        (out/f'acquire_Tm{m}.kpc').write_text(txt,encoding='ascii')
    (out/'README.md').write_text('KnotPlot: read acquisition/acquire_Tm7.kpc (from project root).\\n'
      'This proposes Conway [m,2] generated by the local KnotPlot executable. '
      'Do not label acquired data CERTIFIED until topology/invariant checks pass.\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--mode',choices=['ALL','INDIVIDUAL','BORROMEAN','ACQUIRE'],default='ALL')
    ap.add_argument('--m',type=int,nargs='*',default=[3,4,5,6])
    ap.add_argument('--borromean-m',type=int,nargs=3,default=[3,3,4])
    ap.add_argument('--n',type=int,default=256)
    ap.add_argument('--scale',type=float,default=7.0)
    ap.add_argument('--fold-ratio',type=float,default=0.8)
    a=ap.parse_args()
    if any(m<1 for m in a.m+a.borromean_m):ap.error('m must be positive')
    if a.n<128:ap.error('n >=128')
    if a.scale<=0 or not (0<a.fold_ratio<=1):ap.error('scale positive; fold ratio (0,1]')
    acquire()
    results=[]
    if a.mode in ('ALL','INDIVIDUAL'):
        for m in a.m: results.append(build_individual(m,a.n,a.scale,fold=a.fold_ratio))
    if a.mode in ('ALL','BORROMEAN'):
        results.append(build_borromean(tuple(a.borromean_m),a.n,a.scale,a.fold_ratio))
    print(json.dumps({'n_cases':len(results),'output':[x['case'] for x in results],
                      'status':'STATIC_CANDIDATE_ONLY'},indent=2))

if __name__=='__main__':main()
