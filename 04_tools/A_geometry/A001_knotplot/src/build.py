#!/usr/bin/env python3
"""Diagnostic follow-up to v0.1.0; no dynamical or topological certification."""
from __future__ import annotations
import argparse, hashlib, json, math, sys
from pathlib import Path
import numpy as np
import legacy_build as l

ROOT=Path(__file__).resolve().parents[1]
SRC5=ROOT/'source_native'/'5_2__knotplot_final.txt'
SRC6=ROOT/'source_native'/'6_1__knotplot_final.txt'


def arclength_resample(p, n):
    """Closed, piecewise linear resampling. Not an isotopy proof."""
    p=np.asarray(p,dtype=float)
    edges=np.roll(p,-1,axis=0)-p
    lens=np.linalg.norm(edges,axis=1)
    assert np.min(lens)>1e-10
    distances=np.r_[0,np.cumsum(lens)]
    t=np.arange(n)*distances[-1]/n
    i=np.searchsorted(distances,t,side='right')-1
    return p[i]+((t-distances[i])/lens[i])[:,None]*edges[i]


def unit(v):
    d=np.linalg.norm(v)
    if d<1e-12: raise ValueError('Zero tangent')
    return v/d


def curved_bridge(A,B,t0,t1,n):
    """Cubic Hermite connector with tangency at both endpoints."""
    D=np.linalg.norm(B-A)
    S=min(D*.44,2.3)
    m0=unit(t0)*S
    m1=unit(t1)*S
    u=np.arange(1,n+1)/(n+1)
    u=u[:,None]
    return (2*u**3-3*u**2+1)*A+(-2*u**3+3*u**2)*B + (u**3-2*u**2+u)*m0+(u**3-u**2)*m1


def decorate_smooth(base, source, event, diameter, altitude, nbridge, bead_gap):
    # Keep the carrier except the small marked arc; use preserved knot polygon
    k=event*l.N_PER_EVENT
    N=len(base)
    Aidx=(k-bead_gap)%N
    Bidx=(k+bead_gap)%N
    remain=np.array([base[(Bidx+i)%N] for i in range((Aidx-Bidx)%N+1)])
    A=remain[-1]; B=remain[0]
    src=source.copy()
    kn,edge=l.cut_and_lift_knot(src,0.5*(A+B),B-A,altitude=altitude,diameter=diameter)
    kn=kn[::-1].copy()
    b1=curved_bridge(A,kn[0],A-remain[-2],kn[0]-A,nbridge)
    b2=curved_bridge(kn[-1],B,B-kn[-1],remain[1]-B,nbridge)
    comp=np.vstack([remain,b1,kn,b2])
    return comp,dict(component_type='local knot',cut_edge=int(edge),event=event,join_A=A.tolist(),join_B=B.tolist(),
                     knot_first=kn[0].tolist(),knot_last=kn[-1].tolist(),n_source_points=len(src))


def stat(p):
    v=np.roll(p,-1,axis=0)-p
    L=np.linalg.norm(v,axis=1)
    cosine=np.sum(v*np.roll(v,1,axis=0),axis=1)/(L*np.roll(L,1))
    ang=np.rad2deg(np.arccos(np.clip(cosine,-1,1)))
    return {'length':float(L.sum()),'min_edge':float(L.min()),'max_edge':float(L.max()),
            'edge_ratio':float(L.max()/L.min()),'max_vertex_turn_deg':float(ang.max())}


def produce(tier):
    configs={
      'SMOKE':dict(n_event=24,n_source=144,bridge=12,gap=3),
      'BASIC':dict(n_event=48,n_source=300,bridge=20,gap=6),
    }
    c=configs[tier];l.N_PER_EVENT=c['n_event'];l.R=8.0
    s5=np.loadtxt(SRC5);s6=np.loadtxt(SRC6)
    sk=l.base_components();sources=[s5,s5,s6]
    if c['n_source']!=300:sources=[arclength_resample(x,c['n_source']) for x in sources]
    geom=[];records=[]
    for i,(src,ev) in enumerate(zip(sources,(1,3,5))):
        q,meta=decorate_smooth(sk[i],src,ev,diameter=1.65,altitude=1.55,nbridge=c['bridge'],bead_gap=c['gap'])
        geom.append(q);records.append({**meta,**stat(q)})
    # Validate before emitting any data. Independent topological certification is outstanding.
    link=[l.ringlinking(geom[i],geom[j]) for i,j in ((0,1),(0,2),(1,2))]
    cross={f'{i}-{j}':l.min_segsep(geom[i],geom[j]) for i,j in ((0,1),(0,2),(1,2))}
    self={str(i):l.min_segsep(x,x,True) for i,x in enumerate(geom)}
    print(tier,'npoints',list(map(len,geom)),'cross',cross,'self',self,'link',link,flush=True)
    if max(map(abs,link))>0.03:raise ValueError('Pairwise linking integral drift')
    if min(cross.values())<0.12:raise ValueError('Intercomponent clearance gate')
    if min(self.values())<0.01:raise ValueError('Self-clearance gate')
    out=ROOT/'geometry';out.mkdir(parents=True,exist_ok=True)
    file=out/f'borromean_5_2_5_2_6_1_{tier}.kpt'
    b=l.kpt_bytes(geom);file.write_bytes(b)
    assert all(np.array_equal(a,d) for a,d in zip(geom,l.decode_kpt(b)))
    for i,x in enumerate(geom):
        np.savetxt(out/f'borromean_{tier}_component{i}.xyz',x,fmt='%.17g')
    report={'schema':'SST-PKLSA-BORROMEAN-GO-DIAGNOSTIC-1','version':'0.1.1','tier':tier,
        'scientific_status':'STATIC_DIAGNOSTIC_CANDIDATE_ONLY', 'KnotPlot_runtime':'NOT_TESTED',
        'independent_component_knot_polynomials':'NOT_TESTED',
        'triple_link_invariant':'NOT_TESTED',
        'Euler_dynamics':'NOT_TESTED',
        'component_targets':['5_2','5_2','6_1'],
        'source_sha256':{'5_2':hashlib.sha256(SRC5.read_bytes()).hexdigest(),'6_1':hashlib.sha256(SRC6.read_bytes()).hexdigest()},
        'geometries_sha256':hashlib.sha256(b).hexdigest(),
        'N_points_per_component':list(map(len,geom)),
        'max_turn_deg':[r['max_vertex_turn_deg'] for r in records],
        'records':records,'minimum_cross_segment_clearances':cross,
        'minimum_nonlocal_self_clearances':self,'pairwise_gauss_linking_integrals':link,
        'caveat':'Length minimization is NOT Euler flow; equal provider knot 5_2 duplicated; no full topology certificate.'}
    (ROOT/f'candidate_report_{tier}.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def write_scripts():
    d=ROOT/'diagnostic';d.mkdir(exist_ok=True)
    scripts={
      '00_solver_trefoil_smoke.kpc':'''reset all\ntorus 2 3 128\ninformation\ncoords diagnostic/solver_trefoil_before.xyz\ngo 1\ncoords diagnostic/solver_trefoil_after1.xyz\ninformation\n''',
      '01_borromean_SMOKE_go1.kpc':'''reset all\nload geometry/borromean_5_2_5_2_6_1_SMOKE.kpt\ninformation\ncoords diagnostic/borromean_SMOKE_before.xyz\ncollision fast\ngo 1\ncoords diagnostic/borromean_SMOKE_after1.xyz\ninformation\n''',
      '02_borromean_BASIC_go1.kpc':'''reset all\nload geometry/borromean_5_2_5_2_6_1_BASIC.kpt\ninformation\ncoords diagnostic/borromean_BASIC_before.xyz\ncollision fast\ngo 1\ncoords diagnostic/borromean_BASIC_after1.xyz\ninformation\n''',
      '03_borromean_SMOKE_go32.kpc':'''reset all\nload geometry/borromean_5_2_5_2_6_1_SMOKE.kpt\ninformation\ncollision fast\ncoords diagnostic/borromean_SMOKE_before32.xyz\ngo 32\ncoords diagnostic/borromean_SMOKE_after32.xyz\ninformation\n'''
    }
    for k,v in scripts.items(): (d/k).write_text(v,encoding='ascii')
    for tier in ['SMOKE','BASIC']:
        (ROOT/f'borromean_{tier}_load_only.kpc').write_text(f'reset all\nload geometry/borromean_5_2_5_2_6_1_{tier}.kpt\ninformation\nlength\n',encoding='ascii')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--tier',choices=['SMOKE','BASIC','ALL'],default='ALL')
    args=ap.parse_args();write_scripts()
    for t in (['SMOKE','BASIC'] if args.tier=='ALL' else [args.tier]): produce(t)
if __name__=='__main__':main()
