"""Slow correctness fallback. Production/basic/extended CMD runs require the C++ backend."""
from __future__ import annotations
import math
import numpy as np


def _circumradius(a,b,c):
    A=np.linalg.norm(b-c); B=np.linalg.norm(a-c); C=np.linalg.norm(a-b)
    area2=np.linalg.norm(np.cross(b-a,c-a))
    if area2<=1e-15*(A*B+B*C+C*A+1.0): return float("inf")
    return A*B*C/(2.0*area2)

def _segseg(p1,q1,p2,q2):
    # Same Ericson-style segment closest-point equations as native kernel.
    EPS=1e-15; d1=q1-p1; d2=q2-p2; r=p1-p2
    a=float(d1@d1); e=float(d2@d2); f=float(d2@r); s=t=0.0
    if a<=EPS and e<=EPS: return float(np.linalg.norm(p1-p2)),0.0,0.0,p1,p2
    if a<=EPS: t=float(np.clip(f/e,0,1))
    else:
        c=float(d1@r)
        if e<=EPS: s=float(np.clip(-c/a,0,1))
        else:
            bb=float(d1@d2); den=a*e-bb*bb
            s=float(np.clip((bb*f-c*e)/den,0,1)) if den!=0 else 0.0
            t=(bb*s+f)/e
            if t<0: t=0.0; s=float(np.clip(-c/a,0,1))
            elif t>1: t=1.0; s=float(np.clip((bb-c)/a,0,1))
    cp1=p1+d1*s; cp2=p2+d2*t
    return float(np.linalg.norm(cp1-cp2)),s,t,cp1,cp2

def analyze_geometry(points,component_counts,*,radius=-1.0,contact_tol=0.015,kink_tol=0.015,local_exclusion_frac=0.02,threads=1):
    P=np.asarray(points,float); counts=[int(x) for x in component_counts]
    if sum(counts)!=len(P): raise ValueError("sum(component_counts) mismatch")
    comps=[]; start=0
    for n in counts:
        cum=[0.0]
        for i in range(n): cum.append(cum[-1]+float(np.linalg.norm(P[start+(i+1)%n]-P[start+i])))
        comps.append((start,n,np.asarray(cum),cum[-1])); start+=n
    segs=[]
    for ci,(st,n,cum,L) in enumerate(comps):
        for i in range(n):
            g0=st+i; g1=st+(i+1)%n; ll=float(np.linalg.norm(P[g1]-P[g0])); segs.append((ci,i,g0,g1,P[g0],P[g1],cum[i],ll,L))
    minR=float("inf"); allk=[]
    for ci,(st,n,cum,L) in enumerate(comps):
        for i in range(n):
            R=_circumradius(P[st+(i-1)%n],P[st+i],P[st+(i+1)%n]); minR=min(minR,R); allk.append((ci,i,R,float(cum[i]/L)))
    candidates=[]; minD=float("inf")
    cutoff_lo=0.0 if radius<=0 else 2*radius*(1-contact_tol); cutoff=float("inf") if radius<=0 else 2*radius*(1+contact_tol)
    for i,A in enumerate(segs):
        for j in range(i+1,len(segs)):
            B=segs[j]
            if A[0]==B[0]:
                n=comps[A[0]][1]; d=abs(A[1]-B[1]); d=min(d,n-d); k=max(1,int(math.ceil(local_exclusion_frac*n)))
                if d<=k: continue
            dist,u,v,pa,pb=_segseg(A[4],A[5],B[4],B[5]); minD=min(minD,dist)
            if dist>=cutoff_lo and dist<=cutoff:
                sna=(A[6]+u*A[7])/A[8]; snb=(B[6]+v*B[7])/B[8]; candidates.append((i,j,dist,u,v,pa,pb,sna,snb))
    inferred=radius<=0
    if inferred: radius=min(minR,0.5*minD); candidates=[r for r in candidates if 2*radius*(1-contact_tol)<=r[2]<=2*radius*(1+contact_tol)]
    activeK=[k for k in allk if radius*(1-kink_tol)<=k[2]<=radius*(1+kink_tol)]
    rows=[]; cols=[]; data=[]; contacts=[]; col=0
    for sa,sb,dist,u,v,pa,pb,sna,snb in candidates:
        if dist<=1e-15: continue
        A=segs[sa]; B=segs[sb]; nn=(pa-pb)/dist
        for gv,w in ((A[2],0.5*(1-u)),(A[3],0.5*u),(B[2],-0.5*(1-v)),(B[3],-0.5*v)):
            for ax in range(3): rows.append(3*gv+ax); cols.append(col); data.append(float(w*nn[ax]))
        contacts.append({"column":col,"comp_a":A[0],"seg_a":A[1],"u":u,"s_norm":sna,"comp_b":B[0],"seg_b":B[1],"v":v,"t_norm":snb,"distance":dist}); col+=1
    mean_seg=sum(s[7] for s in segs)/max(1,len(segs)); h=max(1e-9,1e-7*mean_seg); kinks=[]
    for ci,vi,R,sn in activeK:
        st,n,cum,L=comps[ci]; ip=(vi-1)%n; inn=(vi+1)%n
        for q,loc in enumerate((ip,vi,inn)):
            for ax in range(3):
                pts=[P[st+ip].copy(),P[st+vi].copy(),P[st+inn].copy()]; pts[q][ax]+=h; rp=_circumradius(*pts)
                pts=[P[st+ip].copy(),P[st+vi].copy(),P[st+inn].copy()]; pts[q][ax]-=h; rm=_circumradius(*pts); g=(rp-rm)/(2*h)
                if np.isfinite(g): rows.append(3*(st+loc)+ax); cols.append(col); data.append(float(g))
        kinks.append({"column":col,"comp":ci,"vertex":vi,"s_norm":sn,"radius":R}); col+=1
    b=np.zeros(3*len(P))
    for st,n,cum,L in comps:
        for i in range(n):
            gi=st+i; a=P[gi]-P[st+(i-1)%n]; d=P[gi]-P[st+(i+1)%n]; g=a/np.linalg.norm(a)+d/np.linalg.norm(d); b[3*gi:3*gi+3]=g
    return {"rows":np.asarray(rows,np.int64),"cols":np.asarray(cols,np.int64),"data":np.asarray(data,float),"b":b,
            "shape":(3*len(P),col),"contacts":contacts,"kinks":kinks,
            "metrics":{"backend":"python-fallback","component_count":len(comps),"vertex_count":len(P),"segment_count":len(segs),"min_discrete_curvature_radius":minR,"min_nonadjacent_segment_distance":minD,"radius":radius,"radius_inferred":inferred,"contact_tolerance_fraction":contact_tol,"kink_tolerance_fraction":kink_tol,"local_exclusion_fraction":local_exclusion_frac,"active_strut_count":len(contacts),"active_kink_count":len(kinks),"matrix_rows":3*len(P),"matrix_columns":col,"threads":1}}
