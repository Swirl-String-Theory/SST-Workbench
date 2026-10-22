"""A006 v0.5.0 independent output and geometry generation; no old campaigns reused."""
from __future__ import annotations
import hashlib,json,subprocess,sys,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tools'))
from knotplot_io import encode
from smoothclosure_v050 import bounded_smooth,metrics,local_vertex_gap
from selection_v043b import sample_closed,edge_stats,write_xyz3,components_from_xyz,reflected
from orientation_v043b import orient_components,orientation_key
BASE=ROOT/'Input'/'original_frozen'
OUT=ROOT/'Output'/'v050'
STATUS=OUT/'source_reports'
KNOTS=['3_1','4_1','5_1','5_2','6_1','7_1','7_2','8_1','9_1','9_2','10_1','11a247','11a367']

def write_no_overwrite(path,bytes_):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=bytes_:raise FileExistsError('Different generated content: '+str(path))
    else:path.write_bytes(bytes_)

def dump(path,obj):write_no_overwrite(path,(json.dumps(obj,sort_keys=True,indent=2)+'\n').encode())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def generate_master(knot):
    path=BASE/f'{knot}_N2048.xyz'
    if not path.exists():raise FileNotFoundError(path)
    src=np.loadtxt(path)
    revised,meta=bounded_smooth(src)
    outfile=OUT/'masters'/f'{knot}_N2048.xyz'
    text=''.join('%.17g %.17g %.17g\n'%tuple(pt) for pt in revised)
    write_no_overwrite(outfile,text.encode('ascii'))
    meta.update({'knot':knot,'source':str(path.relative_to(ROOT)),'source_sha256':sha(path),
      'geometry_sha256':sha(outfile),'status':'STATIC_CANDIDATE',
      'physical_Euler':'NOT_RUN','topological_equivalence':'UNRESOLVED'})
    dump(STATUS/f'{knot}_smooth_report.json',meta)
    return revised

def individual(knot,n,mirror=False):
    p=np.loadtxt(OUT/'masters'/f'{knot}_N2048.xyz')
    if n!=2048:p,_=sample_closed(p,n)
    if mirror:p=p.copy();p[:,0]*=-1
    metric=metrics(p)
    if metric['min_edge_over_median']<0.18 or metric['max_edge_over_median']>1.6:
        raise ValueError(f'Static spacing reject {knot} N{n}: {metric}')
    state='SHARP_TURN_WARNING' if metric['max_turn_rad']>=1.0 else 'STATIC_CANDIDATE'
    name=f'KNOT_{knot}_N{n:04d}_{"MIRROR" if mirror else "ORIG"}'
    outfile=OUT/'geometry'/f'{name}.xyz'
    write_no_overwrite(outfile,''.join('%.17g %.17g %.17g\n'%tuple(pt) for pt in p).encode('ascii'))
    dump(OUT/'geometry'/f'{name}.json',{'name':name,'kind':'KNOT','n':n,'n_actual':[n],
      'metrics':[metric],'status':state,'source_master':str((OUT/'masters'/f'{knot}_N2048.xyz').relative_to(ROOT)),
      'sha256':sha(outfile),'isotopy':'UNRESOLVED','KnotPlot':'NOT_RUN'})
    return outfile,p

def stage_link(ident,profile,n,scale):
    # Build directly from NEW v0.5.0 smoothed 5_2/6_1 masters in a private stage,
    # reusing the audited periodic carrier transform and strict XYZ checks.
    stage=OUT/'_stage'/f'{ident}_{profile}_N{n:04d}_S{int(scale*1000):04d}'
    ext=stage/'extensions'/'borromean'
    for rel in ('build_borromean.py','whole/build_whole.py','whole/strict_xyz.py',
      'whole/references/borromean_flat.txt','whole/references/borromean_balanced.txt'):
        frm=ROOT/'extensions'/'borromean'/rel;to=ext/rel;to.parent.mkdir(parents=True,exist_ok=True)
        if not to.exists():shutil.copy2(frm,to)
    seed_dir=stage/'output'/'seeds';seed_dir.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((ROOT/'SEED_MANIFEST.json').read_text())
    for knot in ('5_2','6_1'):
        p=np.loadtxt(OUT/'masters'/f'{knot}_N2048.xyz')
        blob=encode([p]);path=seed_dir/f'{knot}_N2048.kpt';write_no_overwrite(path,blob)
        for ent in manifest['seeds']:
            if ent['name']==knot and ent['n']==2048:ent['source_sha256']=sha(path)
    dump(stage/'SEED_MANIFEST.json',manifest)
    builder=ext/'whole'/'build_whole.py'
    cmd=[sys.executable,str(builder),'--root',str(stage),'--composition',ident.replace('_',''),
         '--profiles',profile,'--n-shortest',str(n),'--global-scale',str(scale),'--source-n','2048']
    if not list((stage/'output'/'borromean').glob(f'Borromean_{ident}_{profile}_MIN{n:04d}_S*_v042d.xyz')):
        p=subprocess.run(cmd,cwd=stage,capture_output=True,text=True,timeout=1200)
        if p.returncode:raise RuntimeError('Whole link staging failed: '+p.stdout[-700:]+p.stderr[-1200:])
    found=list((stage/'output'/'borromean').glob(f'Borromean_{ident}_{profile}_MIN{n:04d}_S*_v042d.xyz'))
    if len(found)!=1:raise RuntimeError('Expected exactly one staged link for '+ident)
    return components_from_xyz(found[0]),found[0]

def link(ident,profile,n,scale=0.8,policy='FIXED61',mirror=False,manual_angles=(0.,0.,180.)):
    parts,source=stage_link(ident,profile,n,scale)
    knots=('5_2','5_2','6_1') if ident=='5_5_6' else ('6_1','6_1','5_2')
    parts,orientation=orient_components(parts,policy=policy,manual_angles=manual_angles,root=ROOT,knots=knots)
    if mirror:parts=reflected(parts)
    # Explicit flat three-block numeric contract. No LOAD.kpc or multicomp KPT.
    name=f'LINK_{ident}_{profile}_N{n:04d}_{"MIRROR" if mirror else "ORIG"}_{orientation_key(policy,manual_angles)}'
    dest=OUT/'geometry'/f'{name}.xyz'
    write_xyz3(dest,parts)
    measures=[metrics(p) for p in parts]
    status='STATIC_CANDIDATE' if all(m['max_turn_rad']<1.0 and m['min_edge_over_median']>=.18 for m in measures) else 'SHARP_TURN_WARNING'
    dump(OUT/'geometry'/f'{name}.json',{'name':name,'kind':'LINK','composition':ident,'profile':profile,'minN':n,
      'n_actual':[len(p) for p in parts],'component_knots':knots,'orientation':orientation,
      'status':status,'metrics':measures,'source_stage_sha256':sha(source),'sha256':sha(dest),
      'pairwise_linking_certification':'UNRESOLVED','Milnor_mu123':'UNRESOLVED','Euler':'NOT_RUN','KnotPlot':'NOT_RUN'})
    return dest,parts

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--all-masters',action='store_true');a=ap.parse_args()
    if a.all_masters:
        for knot in KNOTS:generate_master(knot);print(knot,flush=True)
