from __future__ import annotations
import csv, math, sys
from pathlib import Path
import numpy as np
from scipy.sparse import coo_matrix


def _component_meta(points,counts):
    P=np.asarray(points,float); out=[]; st=0
    for n in counts:
        n=int(n); cum=[0.0]
        for i in range(n): cum.append(cum[-1]+float(np.linalg.norm(P[st+(i+1)%n]-P[st+i])))
        out.append((st,n,np.asarray(cum,float),float(cum[-1]))); st+=n
    if st!=len(P): raise ValueError("component count mismatch")
    return out

def _circumradius(a,b,c):
    A=np.linalg.norm(b-c); B=np.linalg.norm(a-c); C=np.linalg.norm(a-b); area2=np.linalg.norm(np.cross(b-a,c-a))
    if area2<=1e-15*(A*B+B*C+C*A+1.0): return float("inf")
    return float(A*B*C/(2*area2))

def _length_gradient(P,meta):
    b=np.zeros(3*len(P))
    for st,n,cum,L in meta:
        for i in range(n):
            gi=st+i; a=P[gi]-P[st+(i-1)%n]; d=P[gi]-P[st+(i+1)%n]
            g=a/np.linalg.norm(a)+d/np.linalg.norm(d); b[3*gi:3*gi+3]=g
    return b

def _locate(P,meta,ci,sn):
    st,n,cum,L=meta[int(ci)]; sn=float(sn)%1.0; target=sn*L; i=int(np.searchsorted(cum,target,side="right")-1); i=max(0,min(n-1,i)); den=cum[i+1]-cum[i]; u=(target-cum[i])/den if den>0 else 0.0
    g0=st+i; g1=st+(i+1)%n; p=P[g0]+u*(P[g1]-P[g0]); return i,g0,g1,float(u),p

def assemble_explicit(points,counts,contact_csv=None,kink_csv=None):
    P=np.asarray(points,float); meta=_component_meta(P,counts); rows=[]; cols=[]; data=[]; contacts=[]; kinks=[]; supplied=[]; col=0
    if contact_csv:
        with open(contact_csv,newline="",encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ca=int(r["comp_a"]); cb=int(r["comp_b"]); sa=float(r["s_norm"]); sb=float(r["t_norm"])
                ia,g0a,g1a,u,pa=_locate(P,meta,ca,sa); ib,g0b,g1b,v,pb=_locate(P,meta,cb,sb); diff=pa-pb; dist=float(np.linalg.norm(diff))
                if dist<=1e-15: continue
                nn=diff/dist
                for gv,w in ((g0a,0.5*(1-u)),(g1a,0.5*u),(g0b,-0.5*(1-v)),(g1b,-0.5*v)):
                    for ax in range(3): rows.append(3*gv+ax); cols.append(col); data.append(float(w*nn[ax]))
                lam=r.get("multiplier",""); supplied.append(float(lam) if lam not in (None,"") else math.nan)
                contacts.append({"column":col,"comp_a":ca,"seg_a":ia,"u":u,"s_norm":sa,"comp_b":cb,"seg_b":ib,"v":v,"t_norm":sb,"distance":dist,"supplied_multiplier":lam}); col+=1
    if kink_csv:
        mean_seg=np.mean([meta[ci][2][-1]/meta[ci][1] for ci in range(len(meta))]); h=max(1e-9,1e-7*float(mean_seg))
        with open(kink_csv,newline="",encoding="utf-8") as f:
            for r in csv.DictReader(f):
                ci=int(r["comp"]); sn=float(r["s_norm"]); st,n,cum,L=meta[ci]; target=(sn%1.0)*L; vi=int(np.argmin(np.minimum(np.abs(cum[:-1]-target),L-np.abs(cum[:-1]-target))))
                ip=(vi-1)%n; inn=(vi+1)%n; R=_circumradius(P[st+ip],P[st+vi],P[st+inn])
                for q,loc in enumerate((ip,vi,inn)):
                    for ax in range(3):
                        pts=[P[st+ip].copy(),P[st+vi].copy(),P[st+inn].copy()]; pts[q][ax]+=h; rp=_circumradius(*pts)
                        pts=[P[st+ip].copy(),P[st+vi].copy(),P[st+inn].copy()]; pts[q][ax]-=h; rm=_circumradius(*pts); g=(rp-rm)/(2*h)
                        if np.isfinite(g): rows.append(3*(st+loc)+ax); cols.append(col); data.append(float(g))
                lam=r.get("multiplier",""); supplied.append(float(lam) if lam not in (None,"") else math.nan)
                kinks.append({"column":col,"comp":ci,"vertex":vi,"s_norm":sn,"radius":R,"supplied_multiplier":lam}); col+=1
    A=coo_matrix((data,(rows,cols)),shape=(3*len(P),col)).tocsr(); A.sum_duplicates(); A.eliminate_zeros(); b=_length_gradient(P,meta)
    return A,b,contacts,kinks,np.asarray(supplied,float),{"backend":"python-explicit-sidecar-assembly","component_count":len(meta),"vertex_count":len(P),"active_strut_count":len(contacts),"active_kink_count":len(kinks),"matrix_rows":A.shape[0],"matrix_columns":A.shape[1]}
