#!/usr/bin/env python3
"""A003 v0.2.6: isolate first scale-dependent pyknotid crossing rejection.

READ-ONLY: the atlas and installed pyknotid package are never modified.
The scoped diagnostic monkeypatch restores pyknotid's helper function immediately.
"""
from __future__ import annotations
import argparse, contextlib, hashlib, inspect, json, math, platform, sys
from pathlib import Path
import numpy as np

ANGLES=(0.63, 1.17)  # frozen A003 v0.2.6 primary projection P1
FROZEN_PAIRS={1200:[(59,599),(65,1041),(381,967),(601,1051)],
              2400:[(118,1199),(131,2083),(762,1934),(1203,2103)]}


def matrix():
    a,b=ANGLES
    ca,sa,cb,sb=math.cos(a),math.sin(a),math.cos(b),math.sin(b)
    return np.array([[1,0,0],[0,cb,-sb],[0,sb,cb]],float) @ np.array([[ca,-sa,0],[sa,ca,0],[0,0,1]],float)


def load(atlas:Path,n:int):
    manifest=json.loads((atlas/'manifest.json').read_text(encoding='utf-8'))
    rows=[r for r in manifest['records'] if r['id']=='fibonacci_torus_F3' and r['sampling']=='uniform_t' and r['points']==n]
    if len(rows)!=1:raise RuntimeError('Atlas manifest record ambiguous/missing for N='+str(n))
    r=rows[0]
    f=(atlas/r['file']).resolve();
    if not f.is_relative_to(atlas.resolve()):raise RuntimeError('path escape')
    sha=hashlib.sha256(f.read_bytes()).hexdigest()
    if sha!=r['sha256']:raise RuntimeError('Atlas hash mismatch: '+str(f))
    p=np.loadtxt(f, dtype=np.float64)
    if p.shape!=(n,3):raise RuntimeError('Unexpected coordinates shape')
    return p@matrix().T, {'filename':r['file'],'sha256':sha}


def default_max_jump_visits(points, segment_index:int, candidate_segment_index:int):
    """Reproduce 0.5.3 find_crossings jump scheduling for one current segment."""
    xy=points[:,:2];n=len(points)
    projected_steps=np.linalg.norm(np.roll(xy,-1,axis=0)-xy,axis=1)
    max_step=float(np.max(projected_steps[:-1]))
    src=points[segment_index+2:]
    i=0;just_jumped=False;target=candidate_segment_index-segment_index-2
    while i<len(src)-1:
        distance=float(np.linalg.norm(xy[segment_index]-src[i,:2]))
        if distance < 2*max_step or just_jumped:
            if i==target:return True
            i+=1;just_jumped=False
        else:
            jumps=max(1,int(math.floor(distance/max_step)-1))
            i+=jumps;just_jumped=True
    return False


def crossing_metrics(points,pairs):
    out=[];n=len(points)
    for k,(i,j) in enumerate(pairs,1):
        u=points[i+1,:2]-points[i,:2];v=points[(j+1)%n,:2]-points[j,:2]
        cp=float(u[0]*v[1]-u[1]*v[0]);norm=float(np.linalg.norm(u)*np.linalg.norm(v))
        sine=abs(cp)/norm
        # This line is the first offending operation in the referenced helpers.py
        rejected=abs(cp)<1e-5
        out.append({'crossing':k,'edge_a':i,'edge_b':j,'raw_cross_product':cp,
            'raw_abs_cross_product':abs(cp),'normalized_abs_sin':sine,
            'fixed_absolute_cutoff':1.e-5,'stock_guard_rejects':bool(rejected),
            'scale_invariant_guard_1e-8_rejects':bool(sine<1e-8),
            'default_max_jump_visits_candidate':default_max_jump_visits(points,i,j)})
    return out


@contextlib.contextmanager
def numpy_old_names():
    added={}
    for name,val in [('float',float),('int',int),('complex',complex)]:
        if name not in np.__dict__:
            setattr(np,name,val);added[name]=val
    try: yield
    finally:
        for name in added: delattr(np,name)


def controlled_provider(points_by_n):
    from pyknotid.spacecurves import Knot,helpers
    source=inspect.getsource(helpers.do_vectors_intersect)
    stock_guard=('0.00001' in source or '1e-05' in source or '1.e-5' in source or '1e-5' in source)
    if not stock_guard:
        raise RuntimeError('Provider helper does not expose expected 1e-5 cutoff; do not assume same root cause')
    orig=helpers.do_vectors_intersect

    def scale_invariant(px,py,dpx,dpy,qx,qy,dqx,dqy):
        cross=dpx*dqy-dpy*dqx
        lens=math.hypot(dpx,dpy)*math.hypot(dqx,dqy)
        if lens==0 or abs(cross) < 1e-8*lens:
            return (0,0.,0.)
        t=((qx-px)*dqy-(qy-py)*dqx)/cross
        if 0.0<t<1.0:
            s=((qx-px)*dpy-(qy-py)*dpx)/cross
            if 0.0<s<1.0:return (1,t,s)
        return (0,-1.,-1.)

    def observe(points):
        # Fresh object: no cached crossings or Gauss code crosses between runs.
        knot=Knot(points,verbose=False)
        raw=knot.raw_crossings(mode='use_max_jump',try_cython=False,recalculate=True)
        gc=knot.gauss_code(mode='use_max_jump',try_cython=False,recalculate=True)
        raw_gc_count=sum(len(x) for x in gc._gauss_code)//2
        # Mutation of this same GaussCode is intentional: show where simplifying first changes it.
        before=str(gc)
        gc.simplify()
        simplified_count=sum(len(x) for x in gc._gauss_code)//2
        after=str(gc)
        try:
            # Knot.alexander_polynomial internally calls gauss_code (cached)
            # then simplification; numeric t=-1 avoids symbolic cost.
            alex=knot.alexander_polynomial(-1)
            value=float(np.real(alex));det=int(round(abs(value)))
        except Exception as e:
            det=None;value=None;error=f'{type(e).__name__}: {e}'
        else:error=None
        return {'raw_crossing_rows':len(raw),'raw_crossing_pairs':len(raw)//2,
            'gauss_code_crossings_before_simplify':raw_gc_count,'gauss_code_crossings_after_simplify':simplified_count,
            'gauss_before':before,'gauss_after':after,'alexander_at_minus_one':value,'determinant':det,'error':error}

    outcomes={}
    for n,points in sorted(points_by_n.items()):
        key=str(n)
        outcomes[key]={}
        # Main stock path and strictly scoped, diagnostic-only variant.
        outcomes[key]['stock_pyknotid']=observe(points)
        helpers.do_vectors_intersect=scale_invariant
        try:outcomes[key]['temporary_scale_invariant_guard_DIAGNOSTIC_ONLY']=observe(points)
        finally:helpers.do_vectors_intersect=orig
    return {'stock_guard_source_has_absolute_1e_minus_5':stock_guard,'do_vectors_intersect_source_sha256':hashlib.sha256(source.encode()).hexdigest(),
        'baseline_and_temporary_patch':outcomes}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--atlas',type=Path,default=Path(__file__).resolve().parent.parent/'A003-v0.1.2')
    ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'FIRST_DIVERGENCE_REPORT.json')
    ap.add_argument('--offline-only',action='store_true',help='Do not import pyknotid')
    args=ap.parse_args()
    report={'schema':'sst.a003.g5.first-divergence/1','analysis_status':'FIRST_BAD_DECISION_NUMERICALLY_IDENTIFIED',
            'scientific_boundary':'Provider implementation control only, not knot or SST physics certification.',
            'source':'A003-v0.1.2; P1 frozen (rz then rx); user v0.2.6 crossing pair fixture',
            'python':sys.version,'numpy_version':np.__version__,'projection_angles_rad':ANGLES,
            'cases':{}, 'stock_pyknotid_reproduction':'NOT_RUN'}
    pts={}
    for n,pairs in FROZEN_PAIRS.items():
        pts[n],meta=load(args.atlas,n)
        report['cases'][str(n)]={'source':meta,'crossings':crossing_metrics(pts[n],pairs)}
    if not args.offline_only:
        try:
            with numpy_old_names():
                import importlib.metadata
                report['pyknotid_version']=importlib.metadata.version('pyknotid')
                report['provider_control']=controlled_provider(pts)
            report['stock_pyknotid_reproduction']='EXECUTED'
        except Exception as ex:
            report['stock_pyknotid_reproduction']='UNRESOLVED'
            report['provider_error']=f'{type(ex).__name__}: {ex}'
    cases=report['cases']
    crit=cases['2400']['crossings'][1]
    ctrl=cases['1200']['crossings'][1]
    report['first_bad_operation']={
        'module':'pyknotid.spacecurves.helpers.do_vectors_intersect',
        'condition':'abs(cross_product(dpx,dpy,dqx,dqy)) < 0.00001',
        'crossing':'F3 N2400 P1 crossing #2, projected edges 131 and 2083',
        'seen_n1200':not ctrl['stock_guard_rejects'], 'wrongly_rejected_n2400':crit['stock_guard_rejects'],
        'normalized_sin_n2400':crit['normalized_abs_sin'],
        'status':'UNDER_REVIEW'
    }
    # Correct status assignment kept explicit; no accidental authority promotion.
    report['first_bad_operation']['status']='CONFIRMED_NUMERIC_THRESHOLD_CROSSING' if crit['stock_guard_rejects'] and not ctrl['stock_guard_rejects'] and crit['normalized_abs_sin']>1e-5 and crit['default_max_jump_visits_candidate'] else 'UNRESOLVED'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'result':report['first_bad_operation'],'provider_status':report['stock_pyknotid_reproduction'],'report':str(args.output)},indent=2))
    return 0 if report['first_bad_operation']['status']=='CONFIRMED_NUMERIC_THRESHOLD_CROSSING' else 2

if __name__=='__main__':raise SystemExit(main())
