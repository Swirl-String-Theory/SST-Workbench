from __future__ import annotations
import numpy as np
from native_ext import polyline_stats,min_segment_distance,doubly_critical_distance

def resample_closed(p,n):
    p=np.asarray(p,float);q=np.vstack([p,p[0]]);seg=np.linalg.norm(np.diff(q,axis=0),axis=1);s=np.r_[0.0,np.cumsum(seg)];L=s[-1]
    if not np.isfinite(L) or L<=0:raise ValueError('degenerate centerline')
    t=np.linspace(0,L,n,endpoint=False);out=np.empty((n,3))
    for k,x in enumerate(t):
        i=min(np.searchsorted(s,x,side='right')-1,len(p)-1);u=(x-s[i])/max(seg[i],1e-300);out[k]=(1-u)*q[i]+u*q[i+1]
    return out

def tangents(p):
    p=np.asarray(p,float);d=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0);n=np.linalg.norm(d,axis=1);return d/np.maximum(n[:,None],1e-300)

def curvature_radius_min(p):
    p=np.asarray(p,float);a=np.roll(p,1,axis=0);b=p;c=np.roll(p,-1,axis=0);ab=np.linalg.norm(b-a,axis=1);bc=np.linalg.norm(c-b,axis=1);ca=np.linalg.norm(a-c,axis=1);area2=np.linalg.norm(np.cross(b-a,c-a),axis=1);R=ab*bc*ca/np.maximum(2*area2,1e-300);R=R[np.isfinite(R)&(R>0)];return float(np.min(R)) if len(R) else float('inf')

def closure_edge_ratio(p):
    p=np.asarray(p,float);internal=np.linalg.norm(np.diff(p,axis=0),axis=1);gap=np.linalg.norm(p[-1]-p[0]);return float(gap/max(float(np.median(internal)),1e-300))

def thickness_proxy(comps,threads=0):
    curv=min(curvature_radius_min(p) for p in comps);dcrit=float('inf');fallback=float('inf')
    for i,a in enumerate(comps):
        ex=max(3,int(round(0.05*len(a))))
        dcrit=min(dcrit,doubly_critical_distance(a,a,True,ex,0.22,threads))
        fallback=min(fallback,min_segment_distance(a,a,True,max(ex,int(round(0.15*len(a)))),threads))
        for j in range(i+1,len(comps)):
            dcrit=min(dcrit,doubly_critical_distance(a,comps[j],False,0,0.22,threads))
            fallback=min(fallback,min_segment_distance(a,comps[j],False,0,threads))
    if not np.isfinite(dcrit):dcrit=fallback
    half=0.5*dcrit
    return {'curvature_radius_min':float(curv),'half_doubly_critical_distance_proxy':float(half),'fallback_half_nonlocal_distance':float(0.5*fallback),'thickness_proxy':float(min(curv,half))}

def geom_stats(comps):
    rows=[dict(polyline_stats(p,True)) for p in comps];L=sum(float(r['length']) for r in rows);return rows,float(L)
