#!/usr/bin/env python3
"""SST Fourier knot geometric seed atlas v0.1.1 (mathematical geometry ONLY).

Usage: python generate.py [--profiles BASIC FULL]
       python generate.py --points 1200 2400 4800 9600
All output coordinates are dimensionless. No vortex model or dynamics claimed.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from pathlib import Path
import numpy as np

PI = np.pi
ROOT = Path(__file__).resolve().parent

PROFILES = {'BASIC': (1200, 2400), 'FULL': (4800, 9600)}

TORUS_PAIRS = {
    '3_1': (2, 3), '5_1': (2, 5), '7_1': (2, 7),
    '8_19': (3, 4), '9_1': (2, 9), '10_124': (3, 5),
    'T_3_7': (3, 7), 'T_4_5': (4, 5), 'T_3_8': (3, 8),
}
TWIST_NAMES = {1:'3_1', 2:'4_1', 3:'5_2', 4:'6_1', 5:'7_2',
               6:'8_1', 7:'9_2', 8:'10_1', 9:'twist_11cross'}

def torus_direct(t, p, q):
    if np.gcd(p, q) != 1 or not (1 < p < q):
        raise ValueError('Torus knot requires 1 < p < q, gcd(p,q)=1')
    return np.column_stack(((2+np.cos(q*t))*np.cos(p*t),
                            (2+np.cos(q*t))*np.sin(p*t), np.sin(q*t)))

def torus_hoste(t, p, q):
    if np.gcd(p, q) != 1 or not (1 < p < q):
        raise ValueError('Torus knot requires 1 < p < q, gcd(p,q)=1')
    return np.column_stack((np.cos(p*t), np.cos(q*t + PI/(2*p)),
                            -np.sin(p*t) + np.cos((q-p)*t + PI/(2*p)-PI/(4*q))))

def kauf_trefoil(t):
    return np.column_stack((np.cos(2*t), np.cos(3*t+.5),
                            .5*np.cos(5*t+.5)+.5*np.sin(3*t+.5)))

def kauf_figure8(t):
    return np.column_stack((np.cos(t)+np.cos(3*t),
                            .6*np.sin(t)+np.sin(3*t),
                            .4*np.sin(3*t)-np.sin(6*t)))

def twist_boocher(t, m):
    """Boocher et al., Theorem 5.5, for m even OR m == 1 mod 4, m>=5."""
    if m >= 2 and m % 2 == 0:
        n=m//2
        ny=2*n+1
        nz2=2*n+3
        phase=(2*n+3-3*PI)/(2*(2*n+1))
    elif m>=5 and m%4==1:
        n=(m-1)//4
        ny=8*n+3
        nz2=8*n+1
        phase=(8*n+1+(8*n+5)*PI)/(2*(8*n+3))
    else:
        raise ValueError('Boocher theorem: m even >=2 or m=4n+1>=5')
    return np.column_stack((np.cos(2*t),np.cos(ny*t+.5),
                            np.cos(2*t+PI/4)+np.cos(nz2*t+phase)))

def twist_lissajous(t, m):
    """Hoste-Zirbel Theorem 4; for m=4n gives K_m; m=4n+3 gives mirror K_m."""
    if m < 3 or m%4 not in (0,3):
        raise ValueError('Lissajous source covers twist m mod 4=0 or 3, m>=3')
    k=m//2 if m%4==0 else (m-1)//2
    ny=2*k+1
    nz=6*k+7
    phase=(6*k+7-3*PI)/(4*k+2)
    return np.column_stack((np.cos(2*t), np.cos(ny*t+.5), np.cos(nz*t+phase)))

def points_by_arclength(original, n):
    # Piecewise-linear resampling of the sampled analytic curve; do not interpret
    # it as an analytic change of parameter or as shape relaxation.
    cyclic=np.vstack((original,original[:1]))
    ds=np.linalg.norm(np.diff(cyclic,axis=0),axis=1)
    cumulative=np.concatenate(([0.],np.cumsum(ds)))
    targets=np.arange(n)*cumulative[-1]/n
    return np.column_stack([np.interp(targets,cumulative,cyclic[:,axis]) for axis in range(3)])

def catalog():
    specs=[]
    for name,(p,q) in TORUS_PAIRS.items():
        specs.append((f'torus_{name}_direct',lambda t,p=p,q=q:torus_direct(t,p,q),
                     {'knot':name,'family':'torus','p':p,'q':q,'variant':'direct_torus',
                      'source':'Kauffman 1997, Sec.7; toroidal trigonometric embedding',
                      'representation':'Fourier-(3,3,1) for generic p<q'}))
        specs.append((f'torus_{name}_hoste',lambda t,p=p,q=q:torus_hoste(t,p,q),
                     {'knot':name,'family':'torus','p':p,'q':q,'variant':'hoste_minimal',
                      'source':'Hoste 2009 Theorem 1, arXiv:0708.3590',
                      'representation':'Fourier-(1,1,2)'}))
    specs += [
      ('kauffman_3_1',kauf_trefoil,{'knot':'3_1','family':'twist','m':1,'variant':'kauffman_1997',
       'source':'Kauffman 1997, Sec.4, arXiv:q-alg/9711013', 'representation':'Fourier-(1,1,2)'}),
      ('kauffman_4_1',kauf_figure8,{'knot':'4_1','family':'twist','m':2,'variant':'kauffman_1997',
       'source':'Kauffman 1997, Sec.5, arXiv:q-alg/9711013', 'representation':'Fourier-(2,2,2)'}),
    ]
    for m,name in TWIST_NAMES.items():
        if m==1: continue
        if m%2==0 or m%4==1:
            specs.append((f'twist_{name}_m{m}_boocher',lambda t,m=m:twist_boocher(t,m),
                          {'knot':name,'family':'twist','m':m,'variant':'boocher',
                           'source':'Boocher et al. 2009 Theorem 5.5', 'representation':'Fourier-(1,1,2)',
                           'chirality':'Unresolved relative to Rolfsen convention; mirror available by z->-z'}))
        if m%4 in (0,3):
            specs.append((f'twist_{name}_m{m}_lissajous',lambda t,m=m:twist_lissajous(t,m),
                          {'knot':name,'family':'twist','m':m,'variant':'hoste_zirbel',
                           'source':'Hoste & Zirbel 2007 Theorem 4', 'representation':'Fourier-(1,1,1)',
                           'chirality':'For m=4n+3 this is the mirror of the source K_m diagram'}))
    return specs

def generate(point_counts=(1200,2400,4800,9600)):
    point_counts = sorted(set(point_counts))
    if any(n < 3 for n in point_counts):
        raise ValueError('Each point count must be >= 3')
    output=ROOT/'xyz'
    output.mkdir(exist_ok=True)
    records=[]
    for key, fun, meta in catalog():
        for n in point_counts:
            t=2*PI*np.arange(n,dtype=float)/n
            raw=fun(t)
            assert raw.shape==(n,3) and np.all(np.isfinite(raw))
            arc=points_by_arclength(raw,n)
            perimeter=float(np.sum(np.linalg.norm(np.diff(np.vstack((raw,raw[0])),axis=0),axis=1)))
            for kind, arr in (('uniform_t',raw),('uniform_s_polyline',arc)):
                name=f'{key}_{kind}_N{n}.xyz'
                path=output/name
                np.savetxt(path,arr,fmt='%.16e')
                profile = next((tag for tag, sizes in PROFILES.items() if n in sizes), 'CUSTOM')
                record={'id':key,**meta,'profile':profile,'points':n,'sampling':kind,'file':f'xyz/{name}',
                        'polyline_length_coordinate_units':perimeter,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                records.append(record)
    (ROOT/'manifest.json').write_text(json.dumps({'version':'v0.1.1','status':'GEOMETRIC_SEEDS_ONLY',
        'profiles':{name:list(sizes) for name,sizes in PROFILES.items()},
        'units':'dimensionless coordinate units','records':records},indent=2)+'\n',encoding='utf-8')
    with (ROOT/'manifest.csv').open('w',newline='',encoding='utf-8') as f:
        cols=['id','knot','family','variant','profile','points','sampling','file','polyline_length_coordinate_units','representation','sha256']
        w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(records)
    print(f'Generated {len(records)} XYZ files for {len(catalog())} analytic seeds')
    print('Files in',output)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--profiles', nargs='+', choices=tuple(PROFILES), default=['BASIC','FULL'],
                        help='Named resolution profiles (default: both)')
    parser.add_argument('--points',type=int,nargs='+',default=None,
                        help='Explicit sample counts; overrides --profiles')
    a=parser.parse_args()
    selected = a.points if a.points is not None else [n for tag in a.profiles for n in PROFILES[tag]]
    generate(selected)
