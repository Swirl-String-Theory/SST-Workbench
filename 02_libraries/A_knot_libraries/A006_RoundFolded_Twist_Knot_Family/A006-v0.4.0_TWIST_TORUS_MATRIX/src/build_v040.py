#!/usr/bin/env python3
"""Reproducible source-native near-circular torus knots and versioned seed census.
Existing 0.3.0 twist seeds are reused as immutable provenance-bearing inputs.
"""
from pathlib import Path
import sys,json,hashlib,math,argparse
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from measure import projection_crossings
from clearance import global_min_nonlocal
from knotplot_io import encode,decode
from tikz_roundfold import assigned_events, alexander
ROOT=Path(__file__).resolve().parents[1]
TORUS={'3_1':3,'5_1':5,'7_1':7,'9_1':9,'11a367':11}
TWIST={'4_1':2,'5_2':3,'6_1':4,'7_2':5,'8_1':6,'9_2':7,'10_1':8,'11a247':9}
ALL=['3_1','4_1','5_1','5_2','6_1','7_1','7_2','8_1','9_1','9_2','10_1','11a247','11a367']
RES=[1024,2048]
RADIUS=78.0;MINOR=1.35

def write_json(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def knot_torus(q,n,R=RADIUS,a=MINOR):
    # T(2,q) embedding: q odd implies gcd(2,q)=1 (one component).
    t=2*np.pi*(np.arange(n)+0.37)/n
    return np.column_stack(((R+a*np.cos(q*t))*np.cos(2*t),(R+a*np.cos(q*t))*np.sin(2*t),a*np.sin(q*t)))
def torus_poly_check(p,q):
    n=len(p);rec=[]
    for c in projection_crossings(p):
        i,j=int(c['segment_a']),int(c['segment_b'])
        va=p[(i+1)%n]-p[i];vb=p[(j+1)%n]-p[j];xy=np.array([c['x'],c['y']]);
        fa=float(np.dot(xy-p[i,:2],va[:2])/np.dot(va[:2],va[:2]));fb=float(np.dot(xy-p[j,:2],vb[:2])/np.dot(vb[:2],vb[:2]));
        sign=int(np.sign(np.linalg.det(np.stack((va[:2],vb[:2])))))
        if not sign:raise ValueError('tangent crossing')
        rec.append({'i':i,'j':j,'s':(i+fa)/n,'t':(j+fb)/n,'signed_xy':sign,'dz':float(c['dz'])})
    if len(rec)!=q:raise ValueError(f'expected {q} crossings, got {len(rec)}')
    events,trace=assigned_events(rec)
    alternating=all(((rec[j]['dz']>0) if side=='a' else (rec[j]['dz']<0))==(k%2==0) for k,(_,j,side) in enumerate(events))
    coeff,det=alexander(trace,rec)
    assert alternating and coeff==[(-1)**i for i in range(q)] and det==q,(coeff,det,alternating)
    return {'crossings':q,'determinant':det,'alexander_coefficients':coeff,'alternating':alternating}
def geometry_report(p):
    e=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    k0=p-np.roll(p,1,axis=0);k1=np.roll(p,-1,axis=0)-p
    chord=np.roll(p,-1,axis=0)-np.roll(p,1,axis=0)
    den=np.linalg.norm(k0,axis=1)*np.linalg.norm(k1,axis=1)*np.linalg.norm(chord,axis=1)
    curv=2*np.linalg.norm(np.cross(k0,k1),axis=1)/den
    dmin=global_min_nonlocal(p)['distance']
    return {'length':float(e.sum()),'edge_cv':float(e.std()/e.mean()),'edge_min':float(e.min()),
            'minimum_nonlocal_centerline_distance':float(dmin),'kappa_max':float(curv.max())}
def build_torus(knot,n):
    q=TORUS[knot];p=knot_torus(q,n)
    topo=torus_poly_check(p,q);geom=geometry_report(p)
    if geom['minimum_nonlocal_centerline_distance']<=0.22 or geom['edge_cv']>0.05:raise ValueError('static qualification failure')
    name=f'{knot}_N{n}';dest=ROOT/'output'/'seeds';dest.mkdir(parents=True,exist_ok=True)
    blob=encode([p]);assert np.array_equal(decode(blob)[0],p)
    (dest/(name+'.kpt')).write_bytes(blob)
    np.savetxt(dest/(name+'.xyz'),p,fmt='%.17g')
    rec={'name':knot,'family':'T(2,q) torus','q':q,'R':RADIUS,'a':MINOR,'a_over_R':MINOR/RADIUS,
         'n':n,'topology_projected':topo,'geometry':geom,'geometry_status':'STATIC_CANDIDATE',
         'KnotPlot_dynamics':'NOT_RUN','Euler_dynamics':'NOT_RUN','source_sha256':sha(dest/(name+'.kpt'))}
    write_json(dest/(name+'_REPORT.json'),rec)
    return rec

def ensure_seeds():
    results=[]
    for knot in ALL:
      for n in RES:
       file=ROOT/'output'/'seeds'/f'{knot}_N{n}.kpt'
       if knot in TORUS:
        r=build_torus(knot,n);results.append(r)
       else:
        rep=ROOT/'output'/'seeds'/f'{knot}_N{n}_ancestor.json'
        if not file.is_file() or not rep.is_file(): raise FileNotFoundError(f'Preserved 0.3.0 seed missing: {file}')
        old=json.loads(rep.read_text());p=np.loadtxt(ROOT/'output'/'seeds'/f'{knot}_N{n}.xyz')
        geo=geometry_report(p)
        if not np.array_equal(decode(file.read_bytes())[0],p) or geo['minimum_nonlocal_centerline_distance']<=.22:raise ValueError(f'old seed mismatch {knot} {n}')
        if old['topology_from_exported_xyz']['determinant']!=2*TWIST[knot]+1: raise ValueError('unexpected twist polynomial')
        rec={'name':knot,'family':'twist','m':TWIST[knot],'n':n,'geometry':geo,
             'source_type':'REUSED_FROM_FROZEN_v0.3.0','geometry_status':'STATIC_CANDIDATE',
             'KnotPlot_dynamics':'NOT_RUN','Euler_dynamics':'NOT_RUN','source_sha256':sha(file)}
        write_json(ROOT/'output'/'seeds'/f'{knot}_N{n}_REPORT.json',rec)
        results.append(rec)
    manifest={'version':'0.4.0','knots':ALL,'resolutions':RES,'count':len(results),
        'torus_construction':'T(2,q) thin toroidal embedding; 78 major and 1.35 minor arbitrary KnotPlot units',
        'name_mapping':{'11a247':'twist 11 crossing (user legacy 11_2)','11a367':'torus T(2,11) (user legacy 11_1)'},
        'source_status':'STATIC_CANDIDATE','physical_dynamics':'UNRESOLVED',
        'seeds':results}
    write_json(ROOT/'SEED_MANIFEST.json',manifest)
    print('Static seed manifest: %s seeds, %s knots'%(len(results),len(ALL)))
    for r in results:
     print('%7s N%-4d  L=%10.4f  min=%7.4f  cv=%.5f  %s'%(r['name'],r['n'],r['geometry']['length'],r['geometry']['minimum_nonlocal_centerline_distance'],r['geometry']['edge_cv'],r['family']))
    return manifest
if __name__=='__main__':ensure_seeds()
