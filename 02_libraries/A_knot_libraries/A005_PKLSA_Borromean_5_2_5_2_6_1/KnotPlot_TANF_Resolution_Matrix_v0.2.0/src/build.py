"""v0.2.3 SmoothClasp static KnotPlot seed generation; no numerical dynamics.
Source: user-provided v0.2.2 build and TikZ 5_2/6_1 approximation.
"""
from __future__ import annotations
from pathlib import Path
import sys,argparse,hashlib,json
import numpy as np
from tikz_roundfold import dense_xyz, EXPECTED, assigned_events, alexander
from near_unknot import approximate_curvature,area_vector,params,toroidal_metrics,winding_number_xy
from smooth_clasp import PROFILES,fold_map,resample_periodic_c2
from knotplot_io import encode,decode
from measure import lengths,projection_crossings
from clearance import global_min_nonlocal
ROOT=Path(__file__).resolve().parents[1]
CLOSE=0.20
MAX_DR=0.02

def write_json(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def topology(p,label):
    cr=[];n=len(p)
    for c in projection_crossings(p):
        i,j=int(c['segment_a']),int(c['segment_b'])
        vi=p[(i+1)%n]-p[i];vj=p[(j+1)%n]-p[j]
        P=np.array([c['x'],c['y']]);q=P-p[i,:2];w=P-p[j,:2]
        fa=float(np.dot(q,vi[:2])/np.dot(vi[:2],vi[:2]));fb=float(np.dot(w,vj[:2])/np.dot(vj[:2],vj[:2]))
        sign=int(np.sign(np.linalg.det(np.stack((vi[:2],vj[:2])))))
        if not sign:raise ValueError('Degenerate projected crossing')
        cr.append({'i':i,'j':j,'s':(i+fa)/n,'t':(j+fb)/n,'signed_xy':sign,'dz':float(c['dz'])})
    if len(cr)!=EXPECTED[label][0]:raise ValueError('Crossing count mismatch')
    ev,trace=assigned_events(cr)
    for k,(_,idx,side) in enumerate(ev):
        cc=cr[idx];actual=(cc['dz']>0) if side=='a' else (cc['dz']<0)
        if actual!=(k%2==0):raise ValueError('Alternating 3D assignment lost')
    poly,det=alexander(trace,cr)
    if (poly,det)!=(EXPECTED[label][1],EXPECTED[label][2]):raise ValueError('Invariant mismatch')
    return {'crossings':len(cr),'alexander_coefficients':poly,'determinant':det,
            'min_abs_crossing_z':float(min(abs(x['dz']) for x in cr)),'alternating_over_under':True}

def script_preset():
    # User's drawing preferences; omit fitto avlength since it rescales the simulation geometry.
    return '\n'.join([
       'reset all','show labels backdrop','mode cb','bradius = 0.2','cradius = 0.1',
       'tanf = on','tanmag = 9','stusplit = 0','dstep = 1',
       f'close = {CLOSE:.2f}',f'max-dr = {MAX_DR:.2f}',''])

def build(label,profile,n):
    cfg=PROFILES[profile]
    # Widen z-crossing lift to reduce sharp local curvature; recompute knot invariants.
    dense,source=dense_xyz(label,width=0.020,height=0.10)
    transformed,mapping=fold_map(dense,profile)
    p=resample_periodic_c2(transformed,n)
    checks=topology(p,label)
    spaces=global_min_nonlocal(p)
    ls=lengths(p)
    kk=approximate_curvature(p)
    if spaces['distance']<CLOSE*1.10:raise ValueError('self-clearance < 1.1*close')
    if spaces['distance']<=2*cfg['visual_cyl_rad']*1.1:raise ValueError('visual-tube overlap')
    if checks['min_abs_crossing_z'] < CLOSE*1.1:raise ValueError('projection z-gap too small')
    if ls['edge_cv']>0.04:raise ValueError('arc length resampling CV too large')
    base=f'SmoothClasp_{label}_{profile}_N{n:04d}'
    dest=ROOT/'output'/'individual'/base;dest.mkdir(parents=True,exist_ok=True)
    blob=encode([p]);back=decode(blob)[0]
    if not np.array_equal(back,p):raise ValueError('KPT binary roundtrip mismatch')
    (dest/f'{base}.kpt').write_bytes(blob)
    np.savetxt(dest/f'{base}.xyz',p,fmt='%.17g')
    rel=f'output/individual/{base}/{base}'
    (dest/f'{base}_LOAD.kpc').write_text(script_preset()+f'load {rel}.kpt\ninformation\nlength\nparameters close\nparameters max-dr\n',encoding='ascii')
    (dest/f'{base}_GO1.kpc').write_text('go 1\n',encoding='ascii')
    (dest/f'{base}_GO32.kpc').write_text('go 32\n',encoding='ascii')
    for snap in ('BEFORE','AFTER1','AFTER33'):
        (dest/f'{base}_SNAP_{snap}.kpc').write_text(f'coords {rel}_{snap}.xyz\n',encoding='ascii')
    cc,R,_=params(transformed)
    torus=toroidal_metrics(p,cc,R)
    record={
      'release':'v0.2.3','status':'DEVELOPMENT_STATIC_CANDIDATE','label':label,'profile':profile,'n':n,
      'basis':'original TikZ vertices; periodic cubic interpolant (not exact Hobby)',
      'deformation':'positive angular-dependent radial diffeomorphism, wider near bottom clasp',
      'source_projection_regularization':source['regularization_P10_dy'],
      'lift_width_fraction':0.020,'lift_height_source_units':0.10,
      'source_mapping':mapping,'knotplot_configuration':{
          'close':CLOSE,'max_dr':MAX_DR,'bradius':0.2,'cradius':0.1,
          'fitto_avlength':'OMITTED_TO_PRESERVE_WORLD_GEOMETRY',
          'KnotPlot_cyl_rad_visual_proposed':cfg['visual_cyl_rad']},
      'topology':checks,'static_nonlocal_clearance':spaces,
      'arclength':ls,'maximum_polygonal_curvature':float(kk.max()),
      'max_turn_angle_rad':float(np.max(np.arctan(kk*np.mean(np.linalg.norm(np.roll(p,-1,axis=0)-p,axis=1))))),
      'toroidal_geometry':torus,'planar_winding':int(winding_number_xy(p,cc)),
      'area_vector':area_vector(p).tolist(),'sha256_kpt':hashlib.sha256(blob).hexdigest(),
      'gates':{'generated':'PASS','alternating_diagram_and_alexander':'PASS','KPT_roundtrip':'PASS',
               'static_clearance_at_close_0p20':'PASS','arclength_spacing':'PASS',
               'polygonal_ambient_isotopy':'UNRESOLVED',
               'KnotPlot_runtime':'NOT_TESTED','KnotPlot_relaxation_topology':'UNRESOLVED',
               'Euler_vortex_stability':'NOT_TESTED','torus_rolling':'UNRESOLVED'}}
    write_json(dest/'REPORT.json',record)
    return record

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('mode',choices=['SMOKE','BASIC','FULL','ALL'],nargs='?',default='BASIC')
    ap.add_argument('--profiles',nargs='+',choices=list(PROFILES),default=list(PROFILES))
    args=ap.parse_args(argv)
    ns=[256,512,1024] if args.mode=='ALL' else [{'SMOKE':256,'BASIC':512,'FULL':1024}[args.mode]]
    records=[]
    for n in ns:
        for profile in args.profiles:
            for label in ['5_2','6_1']:
                r=build(label,profile,n);records.append(r)
                print(f"{label} {profile:8} n={n:4} min={r['static_nonlocal_clearance']['distance']:.4f} "
                      f"max_k={r['maximum_polygonal_curvature']:.4f} det={r['topology']['determinant']}",flush=True)
    write_json(ROOT/'LATEST_BUILD.json',{'version':'0.2.3','mode':args.mode,'cases':len(records),
      'results':[{'label':r['label'],'profile':r['profile'],'n':r['n'],'min_clearance':r['static_nonlocal_clearance']['distance'],
                  'max_discrete_curvature':r['maximum_polygonal_curvature']} for r in records],
      'promotion':'STATIC_CANDIDATE_ONLY','KnotPlot_runtime':'NOT_TESTED','Euler':'NOT_TESTED'})

if __name__=='__main__':main()
