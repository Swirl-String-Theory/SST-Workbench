"""E010 v0.3.6 research-only knot/link seed generator. Python >=3.10.

Generates analytic torus KNOTS and genuinely disjoint multi-component torus LINKS.
No Euler/filament evolution is run and no stability/equilibrium is claimed.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, zipfile
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
CONFIG = HERE/'configs'/'ruban_family.json'
NAME = 'E010_Ruban_Torus_Dynamics_Family_v0.3.6'

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def jwrite(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False)+'\n',encoding='utf-8')

def b_grid(cfg:dict,mode:str):
    if mode=='pilot':
        values=[float(x) for x in cfg['pilot_B0']]
    else:
        f=cfg['fine_B0_range']; n=(f['max']-f['min'])/f['step']
        if abs(n-round(n))>1e-9:raise ValueError('fine range does not divide exactly')
        values=[round(f['min']+i*f['step'],10) for i in range(int(round(n))+1)]
    if not values or len(set(values))!=len(values) or values!=sorted(values) or not all(0<x<1 for x in values):
        raise ValueError('B0 values must be distinct ascending within (0,1)')
    return values

def validate(p:int,q:int,b:float,r0:float,n:int):
    if not (isinstance(p,int) and isinstance(q,int) and p>1 and q>1):raise ValueError('p,q integers >1 required')
    if not (0<b<1 and r0>0 and n>=64):raise ValueError('invalid positive radii or resolution')
    return math.gcd(p,q)

def components(p:int,q:int,b:float,n:int,r0:float=1,theta0:float=0)->list[np.ndarray]:
    """The gcd(p,q) disjoint components of a T(p,q) link on one embedded torus.

    For g=gcd(p,q), each component has reduced winding (p/g,q/g);
    take separate meridional phases 2*pi*j/g at fixed longitudinal phase.
    NOTE: sampling the non-coprime original single curve would merely traverse
    the reduced knot g times, and is NOT a g-component link.
    """
    g=validate(p,q,b,r0,n); P=p//g; Q=q//g
    t=2*np.pi*np.arange(n,dtype=np.float64)/n
    ang=P*t
    cos_a=np.cos(ang); sin_a=np.sin(ang)
    out=[]
    for j in range(g):
        theta=Q*t-theta0+2*np.pi*j/g
        rad=r0*(1+b*np.sin(theta))
        out.append(np.column_stack((rad*cos_a,rad*sin_a,r0*b*np.cos(theta))))
    return out

def sample_ruban(p:int,q:int,b:float,n:int,R0:float=1,theta0:float=0)->np.ndarray:
    if math.gcd(p,q)!=1:raise ValueError('sample_ruban is only for knots; use components for links')
    return components(p,q,b,n,R0,theta0)[0]

def pushforward_affine_shear(points:np.ndarray,r0:float,eps_xy:float=.01,eps_z:float=.005,wave_number:int=2)->np.ndarray:
    """Global C-infinity volume-preserving diffeomorphism applied to ALL link components.

    x'=s*x; y'=y/s; z'=z+eps_z*R0*sin(k*x/R0).
    Jacobian triangular with determinant s*(1/s)*1=1; inverse exists globally.
    """
    if not (0<eps_xy<.05 and 0<=eps_z<.05 and r0>0 and wave_number>=1):raise ValueError('bad perturbation')
    s=1+eps_xy
    out=points.copy(); out[:,0]=s*points[:,0];out[:,1]=points[:,1]/s
    out[:,2]=points[:,2]+eps_z*r0*np.sin(wave_number*points[:,0]/r0)
    return out

def diagnostics(points:np.ndarray):
    ds=np.roll(points,-1,axis=0)-points
    d=np.linalg.norm(ds,axis=1)
    if not (np.isfinite(points).all() and d.min()>0):raise ValueError('nonfinite or degenerate geometry')
    t=ds/d[:,None]
    turns=np.arccos(np.clip(np.sum(t*np.roll(t,-1,axis=0),axis=1),-1,1))
    return {'point_count':len(points),'length_over_R0':float(d.sum()),
            'min_edge_over_R0':float(d.min()),'max_edge_over_R0':float(d.max()),
            'edge_length_cv':float(d.std()/d.mean()),
            'max_polygon_turn_radians':float(turns.max()),
            'reach_continuum':None,'ropelength_diameter':None,'finite_core_certified':False,
            'closed_polygon_seam_included':True,'qualified_for_active_atlas':False}

def xyz(points:np.ndarray)->bytes:
    return ''.join('%.17g %.17g %.17g\n'%(x,y,z) for x,y,z in points).encode()

def min_intercomponent_sampled_distance(parts:list[np.ndarray])->float|None:
    if len(parts)==1:return None
    try:
        from scipy.spatial import cKDTree
    except ImportError as e:
        raise RuntimeError('scipy is required for multi-component separation diagnostics') from e
    ds=[]
    for i in range(len(parts)):
        for j in range(i+1,len(parts)):
            d,_=cKDTree(parts[i]).query(parts[j],k=1,workers=1)
            ds.append(float(np.min(d)))
    return min(ds)

def read_baseline(path:Path|None):
    if path is None:return None,{'status':'NOT_GIVEN'}
    content=None;blob=None
    if path.suffix.lower()=='.zip':
        blob=path.read_bytes()
        with zipfile.ZipFile(path) as z:
            matches=[n for n in z.namelist() if n.endswith('ACTIVE_TOPOLOGY_SET.json')]
            if len(matches)!=1:raise ValueError('Expected a single ACTIVE_TOPOLOGY_SET.json')
            content=z.read(matches[0])
    else:
        matches=list(path.rglob('ACTIVE_TOPOLOGY_SET.json')) if path.is_dir() else [path]
        if len(matches)!=1:raise ValueError('Expected a single ACTIVE_TOPOLOGY_SET.json')
        content=matches[0].read_bytes();blob=content
    d=json.loads(content)
    if d['count']!=len(d['topologies']) or len(set(d['topologies']))!=d['count']:raise ValueError('Invalid baseline')
    return set(d['topologies']),{'status':'REFERENCE_ONLY_UNMODIFIED','sha256':sha(blob),'topology_set_sha256':sha(content),'active_count':d['count']}

def count_summary(cfg:dict,mode:str):
    bv=b_grid(cfg,mode)
    knots=sum(math.gcd(f['p'],f['q'])==1 for f in cfg['families'])
    links=len(cfg['families'])-knots
    comp=sum(math.gcd(f['p'],f['q']) for f in cfg['families'])
    shapes=len(cfg['families'])*len(bv)
    return dict(version='v0.3.6',mode=mode,knot_family_count=knots,link_family_count=links,
       family_count=len(cfg['families']),component_total_per_B=comp,geometry_count=shapes,
       knot_geometry_count=knots*len(bv),link_geometry_count=links*len(bv),
       coordinate_files_nominal=comp*len(bv),coordinate_files_perturbed=comp*len(bv),
       point_count_per_component=cfg['point_count'],B0_values=bv,Lambda_values=cfg['Lambda'],
       delta_over_R0=cfg['delta_over_R0'],scenario_count=shapes*len(cfg['Lambda'])*len(cfg['delta_over_R0']),
       independent_source_groups=1,scientific_status='GEOMETRY_ONLY_DYNAMICS_NOT_RUN',
       geometry_source='ANALYTIC_TORUS_FORMULA_NOT_KNOTPLOT_COORDINATE_IMPORT')

def build(cfg:dict,out:Path,mode:str='pilot',baseline:Path|None=None,dry_run:bool=False):
    summary=count_summary(cfg,mode)
    seen=set()
    for f in cfg['families']:
        pair=(f['p'],f['q'])
        if pair in seen:raise ValueError(f'duplicate torus family {pair}')
        seen.add(pair)
        g=validate(*pair,summary['B0_values'][0],cfg['geometry_R0'],cfg['point_count'])
        if g not in (1,3):raise ValueError(f'unexpected component count for {pair}')
        if f.get('declared_component_count',g)!=g:raise ValueError(f'wrong declared component count for {pair}')
    if dry_run:return summary
    active,base_info=read_baseline(baseline)
    if out.exists():raise FileExistsError('Existing outputs protected: '+str(out))
    out.mkdir(parents=True)
    summary['baseline']=base_info
    records=[]; scenarios=[]; compare=[]
    for fi,f in enumerate(cfg['families']):
        p,q=f['p'],f['q']; g=math.gcd(p,q); ident=f'T_{p}_{q}'
        for b in summary['B0_values']:
            seed_id=f'{ident}_B{round(b*10000):04d}_N{cfg["point_count"]}'
            orig=components(p,q,b,cfg['point_count'],cfg['geometry_R0'],cfg['theta0'])
            pert=[pushforward_affine_shear(x,cfg['geometry_R0'],cfg['perturbation_policy']['epsilon_xy'],cfg['perturbation_policy']['epsilon_z_shear'],p) for x in orig]
            part_entries=[]
            for j,(x,y) in enumerate(zip(orig,pert)):
                part_suffix='' if g==1 else f'_C{j:02d}'
                org_rel=Path('seeds')/ident/(seed_id+part_suffix+'.xyz')
                per_rel=Path('seeds_perturbed')/ident/(seed_id+part_suffix+'_eps01.xyz')
                raw0=xyz(x);raw1=xyz(y)
                for rel,dat in ((org_rel,raw0),(per_rel,raw1)):
                    dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(dat)
                part_entries.append({'component_index':j,'xyz_path':org_rel.as_posix(),'sha256':sha(raw0),
                  'perturbed_xyz_path':per_rel.as_posix(),'perturbed_sha256':sha(raw1),'geometry_metrics':diagnostics(x)})
            sep=min_intercomponent_sampled_distance(orig)
            sep_pert=min_intercomponent_sampled_distance(pert)
            rec={'seed_id':seed_id,'p':p,'q':q,'B0':b,'R0':cfg['geometry_R0'],'theta0':cfg['theta0'],
                 'parametric_embedding':ident,'object_type':'torus_knot' if g==1 else 'torus_link',
                 'component_count':g,'reduced_component_winding':{'p':p//g,'q':q//g},
                 'expected_pairwise_linking_number':p*q//(g*g) if g>1 else None,
                 'topology_id':f.get('topology_id'),'is_member_of_active_v034':(None if active is None else (f.get('topology_id') in active if f.get('topology_id') else False)),
                 'components':part_entries,'xyz_path':part_entries[0]['xyz_path'] if g==1 else None,
                 'perturbed_xyz_path':part_entries[0]['perturbed_xyz_path'] if g==1 else None,
                 'total_length_over_R0':sum(x['geometry_metrics']['length_over_R0'] for x in part_entries),
                 'minimum_sampled_intercomponent_distance_over_R0':sep,
                 'minimum_sampled_intercomponent_distance_perturbed_over_R0':sep_pert,
                 'sampled_distance_is_not_continuum_certificate':True,
                 'analytic_topology_certificate':('EMBEDDED_COPRIME_TORUS_KNOT_UNPERTURBED' if g==1 else 'DISJOINT_G_COMPONENT_TORUS_LINK_UNPERTURBED'),
                 'perturbed_topology_certificate':'GLOBAL_VOLUME_PRESERVING_SMOOTH_DIFFEO_CONTINUUM',
                 'polygon_embedding_certificate':'NOT_RUN',
                 'perturbation':'GLOBAL_VOLUME_PRESERVING_XY_AFFINE_AND_Z_SHEAR',
                 'source_class':'ANALYTIC_GENERATION_NOT_INDEPENDENT_KNOTPLOT',
                 'source_independence_group':cfg['source_independence_group'],
                 'reference_tag':f.get('source_reference_tag','analytical'),
                 'literature_class':f.get('literature_class','NOT_EVALUATED'),
                 'published_figure':f.get('figure'),
                 'vortexlab_historical_state':f.get('vortexlab_historical_state'),
                 'dynamic_stability':'NOT_TESTED','finite_core_qualified':False,
                 'state':'RESEARCH_GEOMETRY_UNADMITTED'}
            records.append(rec)
            compare.append({'seed_id':seed_id,'object_type':rec['object_type'],'component_count':g,
              'B0':b,'Lambda':'NOT_SELECTED','total_length_over_R0':rec['total_length_over_R0'],
              'sampled_intercomponent_gap_over_R0':sep if sep is not None else '',
              'ropelength':'','euler_residual':'','survival_time':'','status':'NOT_EVALUATED'})
            for lam in cfg['Lambda']:
                for delta in cfg['delta_over_R0']:
                    xi=math.exp(-float(lam))
                    scenarios.append({'seed_id':seed_id,'object_type':rec['object_type'],
                      'component_count':g,'B0':b,'Lambda':lam,'xi_over_R0':xi,
                      'r0_over_xi':b/xi,'delta_over_R0':delta,
                      'slender_core_review':'REVIEW' if b/xi<4 else 'NO_AUTOMATIC_QUALIFICATION',
                      'core_overlap_review':'REVIEW' if sep is not None and sep<2*xi else 'NO_AUTOMATIC_QUALIFICATION',
                      'separation_heuristic_is_not_a_certification':True,
                      'dynamics_backend':'NOT_RUN','gate':'PENDING'})
    if len(records)!=summary['geometry_count'] or len(scenarios)!=summary['scenario_count']:raise AssertionError('incorrect generated totals')
    jwrite(out/'FAMILY_INDEX.json',{'schema':'E010-RUBAN-FAMILY-INDEX-2','version':'v0.3.6',
       'source_contract_sha256':sha(CONFIG.read_bytes()),'baseline':base_info,'seed_count':len(records),
       'research_only':True,'production_admission':False,'seeds':records})
    jwrite(out/'DYNAMICS_PENDING.json',{'status':'NOT_RUN','scenario_count':len(scenarios),
       'scenarios':scenarios,'note':'These are proposed scenarios, not evaluated Euler or filament dynamics.'})
    jwrite(out/'BUILD_SUMMARY.json',summary)
    with (out/'GEOMETRY_VS_SURVIVAL.csv').open('w',newline='',encoding='utf-8') as h:
        w=csv.DictWriter(h,fieldnames=list(compare[0]));w.writeheader();w.writerows(compare)
    entries=[]
    for fp in sorted(out.rglob('*')):
        if fp.is_file():entries.append(sha(fp.read_bytes())+'  '+fp.relative_to(out).as_posix())
    (out/'MANIFEST_SHA256.txt').write_text('\n'.join(entries)+'\n',encoding='utf-8')
    return summary

def package(out:Path,archive:Path):
    if archive.exists():raise FileExistsError('archive already exists: '+str(archive))
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
        for fp in sorted(out.rglob('*')):
            if fp.is_file():z.write(fp,arcname=out.name+'/'+fp.relative_to(out).as_posix())
    (archive.parent/(archive.name+'.sha256')).write_text(sha(archive.read_bytes())+'  '+archive.name+'\n')

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--mode',choices=['pilot','fine'],default='pilot')
    a.add_argument('--output-root',type=Path)
    a.add_argument('--base-view',type=Path)
    a.add_argument('--dry-run',action='store_true')
    a.add_argument('--archive',action='store_true')
    args=a.parse_args()
    cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
    out=args.output_root or (HERE.parent/(NAME+'-'+args.mode+'-outputs'))
    result=build(cfg,out,args.mode,args.base_view,args.dry_run)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if args.archive and not args.dry_run:
        f=out.parent/(NAME+'_'+args.mode+'_outputs.zip');package(out,f)
        print('Archive:',f)

if __name__=='__main__':main()
