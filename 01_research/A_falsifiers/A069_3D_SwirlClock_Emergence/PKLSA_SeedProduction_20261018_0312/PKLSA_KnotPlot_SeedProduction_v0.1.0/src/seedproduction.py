#!/usr/bin/env python3
"""Reproducible static geometry seeds from notebook 2015 (no dynamics certification).

Python 3.10+, numpy. No physical units are attached to the historical coordinates.
The 'KnotPlot 1.0' LOCD writer follows Scharein's public format description.
It cannot certify the ability of a particular KnotPlot installation to load files:
run the separately described import/roundtrip check on your own executable.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
import struct
from pathlib import Path
import numpy as np

VERSION='0.1.0'
RESOLUTIONS=(128,256,512,1024)


def historical(t, family):
    if family=='A':
        return np.stack((np.cos(t)+1.5*np.cos(2*t),
             np.sin(t)-1.5*np.sin(2*t), 0.35*np.sin(3*t)),axis=-1)
    if family=='B':
        return np.stack(((2+np.cos(3*t))*np.cos(2*t),
             (2+np.cos(3*t))*np.sin(2*t),np.sin(3*t)),axis=-1)
    raise ValueError(family)


def arc_sample(family,n,m=65536):
    """Periodic arclength reparameterization by linear interpolation of dense analytic samples."""
    if n<32 or m<n*8: raise ValueError('insufficient sampling resolution')
    t=2*np.pi*np.arange(m+1)/m
    p=historical(t,family)
    seg=np.linalg.norm(np.diff(p,axis=0),axis=1)
    cum=np.r_[0.,np.cumsum(seg)]
    targets=np.arange(n)*cum[-1]/n
    pts=np.column_stack([np.interp(targets,cum,p[:,j]) for j in range(3)])
    return pts,float(cum[-1])


def length_and_cv(p):
    lens=np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1)
    L=float(np.sum(lens))
    return L,float(np.std(lens)/np.mean(lens)),float(np.max(lens)/np.min(lens))


def projected_crossings(p):
    """Counts transverse segment crossings with signed over/under order.

    A *generic* x-y projection is required. This is a diagnostic for this
    already-identified 3_1 construction, NOT a general isotopy certificate.
    """
    xy=p[:,:2]
    edge=np.roll(p,-1,axis=0)-p
    n=len(p)
    rows=[]
    for i in range(n):
        j=np.arange(i+2,n-(1 if i==0 else 0))
        if len(j)==0: continue
        v=xy[j]-xy[i]
        r=edge[i,:2]; s=edge[j,:2]
        den=r[0]*s[:,1]-r[1]*s[:,0]
        valid=np.abs(den)>1e-13
        a=np.full(len(j),np.nan);b=np.full(len(j),np.nan)
        a[valid]=(v[valid,0]*s[valid,1]-v[valid,1]*s[valid,0])/den[valid]
        b[valid]=(v[valid,0]*r[1]-v[valid,1]*r[0])/den[valid]
        select=(a>1e-9)&(a<1-1e-9)&(b>1e-9)&(b<1-1e-9)
        for ix in np.flatnonzero(select):
            k=int(j[ix])
            za=p[i,2]+a[ix]*edge[i,2];zb=p[k,2]+b[ix]*edge[k,2]
            if abs(za-zb)<1e-9: raise ValueError('3D polygon intersection candidate')
            orient=float(den[ix]) if za>zb else -float(den[ix])
            rows.append((i,k,int(np.sign(orient)),float(abs(za-zb))))
    return rows


def tilt(p):
    """Fixed proper rotation prevents vertex-aligned projection singularities."""
    ax,ay=0.013,0.017
    cx,sx=math.cos(ax),math.sin(ax)
    cy,sy=math.cos(ay),math.sin(ay)
    Rx=np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    Ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    return p@(Ry@Rx).T


def txt_bytes(p):
    return ''.join('%.17g %.17g %.17g\n'%tuple(x) for x in p).encode('ascii')


def kpt_bytes(p):
    # KnotPlot header + form-feed/newline, component start, closed flag,
    # big-endian LOCD 64-bit coordinates, terminal endf field.
    coords=np.asarray(p,dtype='>f8').tobytes(order='C')
    return (b'KnotPlot 1.0\n\x0c\n' + b'comp' + b'Attr'
            + struct.pack('>I',1) + b'LOCD' + struct.pack('>I',len(coords))
            + coords + b'endf')


def decode_kpt(data):
    head=b'KnotPlot 1.0\n\x0c\ncompAttr\x00\x00\x00\x01LOCD'
    if not data.startswith(head) or not data.endswith(b'endf'):
        raise ValueError('LOCD envelope mismatch')
    nbytes=struct.unpack('>I',data[len(head):len(head)+4])[0]
    b=data[len(head)+4:-4]
    if nbytes!=len(b) or nbytes%24: raise ValueError('LOCD payload bad')
    return np.frombuffer(b,dtype='>f8').reshape(-1,3).astype(np.float64)


def atomic_write(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(content)
    return hashlib.sha256(content).hexdigest()


def main():
    pa=argparse.ArgumentParser(description=__doc__)
    pa.add_argument('--out', default='production_out',type=Path)
    pa.add_argument('--resolutions', nargs='+', type=int,default=list(RESOLUTIONS))
    args=pa.parse_args()
    out=args.out.resolve()
    if any(n<32 or n>8192 for n in args.resolutions):
        pa.error('supported N from 32 to 8192')
    if out.exists() and any(out.iterdir()):
        pa.error('output directory is not empty; immutable production only')
    out.mkdir(parents=True,exist_ok=True)
    (out/'checkpoints').mkdir(exist_ok=True)
    rows=[]
    for fam in ['A','B']:
        for parity in ['base','mirror_z']:
            for n in sorted(set(args.resolutions)):
                raw,analytic_length=arc_sample(fam,n)
                p=raw.copy()
                if parity=='mirror_z':p[:,2]*=-1.
                pl,cv,ratio=length_and_cv(p)
                # Crossing signs must reverse for a *true* reflection.
                crossings=projected_crossings(tilt(p))
                wr=int(sum(c[2] for c in crossings))
                expected=(3 if fam=='A' else -3)*(-1 if parity=='mirror_z' else 1)
                passed=(len(crossings)==3 and wr==expected and cv<0.02
                        and np.isfinite(p).all() and np.min(np.linalg.norm(np.diff(p,axis=0),axis=1))>0)
                key=f'notebook2015_{fam}_{parity}_N{n:04d}'
                tx=out/'geometry'/(key+'.txt')
                kp=out/'geometry'/(key+'.kpt')
                txtsha=atomic_write(tx,txt_bytes(p)); kpsha=atomic_write(kp,kpt_bytes(p))
                assert np.array_equal(decode_kpt(kp.read_bytes()),p)
                rows.append(dict(id=key,family=fam,parity=parity,n=n,component_count=1,
                                 claimed_topology='3_1',expected_projection_writhe=expected,
                                 observed_projection_writhe=wr,projection_crossings=len(crossings),
                                 analytic_arc_length=analytic_length,polygon_length=pl,
                                 edge_cv=cv,edge_ratio=ratio,status=('STATIC_QA_PASS' if passed else 'QUARANTINE_QA_FAIL'),
                                 source='notebook_2015_page_32' if fam=='A' else 'notebook_2015_page_66',
                                 lineage_parent=f'notebook2015_{fam}_base',
                                 independence_group='2015_notebooks_same_author',
                                 physical_units='NONE_DIMENSIONLESS',
                                 physical_status='NOT_QUALIFIED',
                                 geometry_txt=f'geometry/{tx.name}',geometry_txt_sha256=txtsha,
                                 knotplot_locd=f'geometry/{kp.name}',knotplot_locd_sha256=kpsha))
                # This diagnostic KPC does not evolve geometry, change sliders, or claim convergence.
                script=('reset all\n'+f'load geometry/{kp.name}\n'+
                        'information\nlength\nparameters\n'+
                        f'coords checkpoints/{key}_roundtrip.txt\n'+
                        f'save checkpoints/{key}_roundtrip.txt ascii\n')
                atomic_write(out/'kpc_diagnostic'/f'{key}.kpc',script.encode('ascii'))
    names=list(rows[0].keys())
    with (out/'manifest.csv').open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=names);w.writeheader();w.writerows(rows)
    d=dict(schema='PKLSA_GEOMETRY_SEED_BUNDLE_0.1',version=VERSION,
           role='STATIC_GEOMETRY_ONLY',physical_certification='NONE',
           canonical_E010_modified=False,locked_source_or_external_KnotPlot_execution='NO',
           formula_2015={'A':'(cos(t)+1.5*cos(2t), sin(t)-1.5*sin(2t), 0.35*sin(3t))',
                         'B':'((2+cos(3t))*cos(2t), (2+cos(3t))*sin(2t), sin(3t))'},
           param_interval='[0, 2*pi)',units='dimensionless',
           notebook_parent_provider='notebook_2015_same_author',
           point_ladder=sorted(set(args.resolutions)),
           mirror_operator='(x,y,z)->(x,y,-z)',
           disclaimer='KnotPlot imports/roundtrips and vortex dynamics NOT executed here',
           source_count=2,geometries=len(rows),static_checks_passed=sum(x['status']=='STATIC_QA_PASS' for x in rows))
    atomic_write(out/'RELEASE_CANDIDATE.json',(json.dumps(d,sort_keys=True,indent=2)+'\n').encode())
    print(json.dumps({'result': 'PASS' if d['static_checks_passed']==len(rows) else 'FAIL',
                      'geometries':len(rows),'passed':d['static_checks_passed'],
                      'output':str(out)},indent=2))
    if d['static_checks_passed']!=len(rows):raise SystemExit(1)

if __name__=='__main__':main()
