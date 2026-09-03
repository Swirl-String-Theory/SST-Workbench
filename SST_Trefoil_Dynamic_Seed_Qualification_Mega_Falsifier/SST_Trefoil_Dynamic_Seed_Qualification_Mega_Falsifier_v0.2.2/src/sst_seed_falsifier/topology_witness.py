"""Independent geometric trefoil diagram witness, without a knot-name lookup.

A generic three-crossing diagram with Gauss pattern abcabc, alternating
over/under and equal crossing signs is a trefoil (chirality immaterial here).
Floating-point margins are recorded. This is NOT interval arithmetic or a
certified ambient-isotopy proof. It only accepts, never classifies a rejection.
"""
import numpy as np


def projection_diagram(x, rotation, margin=1e-7):
    p = np.asarray(x,float) @ np.asarray(rotation,float).T
    p = p / max(float(np.linalg.norm(np.ptp(p,axis=0))),1e-30)
    n = len(p); events=[]; signs=[]; crossings=[]; degenerate=False
    edges=np.roll(p,-1,axis=0)-p
    for i in range(n):
        js=np.arange(i+2,n)
        if i==0: js=js[js!=n-1]
        if not len(js): continue
        a=edges[i,:2]; b=edges[js,:2]; c=p[js,:2]-p[i,:2]
        det=a[0]*b[:,1]-a[1]*b[:,0]
        good=np.abs(det)>1e-15
        u=np.full(len(js),np.inf); v=u.copy()
        u[good]=(c[good,0]*b[good,1]-c[good,1]*b[good,0])/det[good]
        v[good]=(c[good,0]*a[1]-c[good,1]*a[0])/det[good]
        hits=(u>=-margin)&(u<=1+margin)&(v>=-margin)&(v<=1+margin)
        # Collinear projected nonlocal edges make this projection unusable.
        collinear=(~good)&(np.abs(c[:,0]*a[1]-c[:,1]*a[0])<1e-13)
        if np.any(collinear): degenerate=True
        for k in np.where(hits)[0]:
            j=int(js[k]); dz=p[i,2]+u[k]*edges[i,2]-p[j,2]-v[k]*edges[j,2]
            angle_margin=abs(det[k])/max(np.linalg.norm(a)*np.linalg.norm(b[k]),1e-30)
            numeric_margin=min(u[k],1-u[k],v[k],1-v[k],abs(dz),angle_margin)
            if numeric_margin <= margin: degenerate=True
            label=len(signs)
            signs.append(int(np.sign(det[k]*dz)))
            events.extend([(float(i+u[k]),label,int(dz>0)),(float(j+v[k]),label,int(dz<0))])
            crossings.append({'segments':[i,j],'parameters':[float(u[k]),float(v[k])],
                              'depth_difference':float(dz),'numeric_margin':float(numeric_margin)})
    events.sort(); labels=[e[1] for e in events]; overs=[e[2] for e in events]
    trefoil=(not degenerate and len(signs)==3 and len(set(signs))==1 and signs[0]!=0
             and labels[:3]==labels[3:] and len(set(labels[:3]))==3
             and all(overs[i]!=overs[(i+1)%6] for i in range(6)))
    return {'accepted':bool(trefoil),'crossing_count':len(signs),'degenerate':bool(degenerate),
            'gauss_labels':labels,'over_under':overs,'crossing_signs':signs,'crossings':crossings}


def trefoil_witness(x, projections=96, seed=93017):
    rng=np.random.default_rng(seed)
    for attempt in range(projections):
        q,_=np.linalg.qr(rng.normal(size=(3,3)))
        if np.linalg.det(q)<0: q[:,0]*=-1
        report=projection_diagram(x,q)
        if report['accepted']:
            return {**report,'status':'SUPPORTED_TREFOIL_DIAGRAM','projection_index':attempt,
                    'rotation':q.tolist(),'precision':'float64_with_margins_not_interval_certified'}
    return {'accepted':False,'status':'UNVERIFIED_NO_TREFOIL_DIAGRAM_FOUND','projections_tried':projections}
