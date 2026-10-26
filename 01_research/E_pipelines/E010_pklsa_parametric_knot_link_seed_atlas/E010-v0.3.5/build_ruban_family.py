"""Non-destructive research-only E010 Ruban torus-knot subfamily builder.

Requires Python 3.10+ and numpy. It creates INITIAL CONDITIONS, NOT stability results.
Geometry is dimensionless with R0=1; no automatic PKLSA admissions.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import zipfile

import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PACKAGE_DIR / 'configs' / 'ruban_family.json'
OUT_NAME = 'E010_Ruban_Torus_Dynamics_Family_v0.3.5-outputs'
ARCHIVE_NAME = 'E010_Ruban_Torus_Dynamics_Family_v0.3.5_outputs.zip'


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def validate_torus(p: int, q: int, b0: float, r0: float, n: int) -> None:
    if p <= 1 or q <= 1 or math.gcd(p, q) != 1:
        raise ValueError('single knot requires coprime integers p,q > 1')
    if not (0.0 < b0 < 1.0 and r0 > 0 and n >= 64):
        raise ValueError('require 0<B0<1, R0>0, N>=64')


def sample_ruban(p: int, q: int, b0: float, n: int, R0: float=1.0, theta0: float=0.0) -> np.ndarray:
    """Ruban (2018), n_vortex_filaments=1, equations (1)-(3), t=0.

    R=R0*(1+B0*sin(q*beta-theta0)), z=R0*B0*cos(q*beta-theta0).
    """
    validate_torus(p,q,b0,R0,n)
    beta = 2*np.pi*np.arange(n, dtype=np.float64)/float(n)
    angle=q*beta-theta0
    rr=R0*(1+b0*np.sin(angle))
    return np.column_stack([rr*np.cos(p*beta), rr*np.sin(p*beta), R0*b0*np.cos(angle)])


def ruban_inspired_perturbation(points: np.ndarray, p: int, q: int, eps_xy:float=0.01, eps_z:float=0.005) -> np.ndarray:
    """Deterministic broken-axial-symmetry initial condition, NOT a Ruban figure reconstruction.

    Inspired by Ruban 2018 arXiv:1806.10783 page 5; the published computations
    also vary azimuthal phase and perturbation patterns.
    """
    if not (0 < eps_xy < 0.05 and 0 <= eps_z < 0.05):
        raise ValueError('perturbation amplitude outside deliberately conservative generator bounds')
    x=points.copy()
    x[:,0] *= 1.0+eps_xy
    x[:,1] *= 1.0/(1.0+eps_xy)
    if q%2==0:
        beta=2*np.pi*np.arange(len(points),dtype=float)/len(points)
        x[:,2] *= (1.0+eps_z*np.sin(p*beta))
    return x


def geometric_diagnostics(points: np.ndarray) -> dict:
    # Discrete curvature is only a diagnostic; NEVER infer a certified reach or ropelength.
    edges = np.roll(points,-1,axis=0)-points
    el = np.linalg.norm(edges,axis=1)
    n = len(points)
    tang = edges/np.maximum(el[:,None],1e-300)
    turn = np.arccos(np.clip(np.einsum('ij,ij->i',tang,np.roll(tang,-1,axis=0)),-1.0,1.0))
    return {
        'point_count': n,
        'length_over_R0':float(el.sum()),
        'min_edge_norm_R0':float(np.min(el)),
        'max_edge_norm_R0':float(np.max(el)),
        'edge_length_cv':float(np.std(el)/np.mean(el)),
        'max_polygon_turn_radians':float(np.max(turn)),
        'self_intersection_continuum':'NONE_BY_TORUS_COPRIMALITY_IF_0_LT_B_LT_1',
        'ropelength_diameter':None,
        'reach':None,
        'ruban_lifetime':None,
        'qualified_for_active_atlas':False
    }


def coordinates_bytes(points: np.ndarray) -> bytes:
    return ''.join(f'{x:.17g} {y:.17g} {z:.17g}\n' for x,y,z in points).encode('utf-8')


def read_active_baseline(path: Path | None) -> tuple[set[str] | None, dict]:
    if path is None:
        return None, {'status':'NOT_GIVEN'}
    path = path.resolve()
    if path.suffix.lower() == '.zip':
        blob = path.read_bytes()
        with zipfile.ZipFile(path) as z:
            candidates=[n for n in z.namelist() if n.endswith('/ACTIVE_TOPOLOGY_SET.json') or n=='ACTIVE_TOPOLOGY_SET.json']
            if len(candidates)!=1: raise ValueError('base ZIP has no unique ACTIVE_TOPOLOGY_SET.json')
            content=z.read(candidates[0])
    else:
        f = path/'ACTIVE_TOPOLOGY_SET.json'
        if not f.exists():
            matches=list(path.rglob('ACTIVE_TOPOLOGY_SET.json'))
            if len(matches)!=1: raise ValueError('base directory has no unique ACTIVE_TOPOLOGY_SET.json')
            f=matches[0]
        content=f.read_bytes()
        blob=content
    d=json.loads(content)
    if d.get('count')!=len(d.get('topologies',[])) or len(set(d.get('topologies',[])))!=d['count']:
        raise ValueError('baseline topology count inconsistent or duplicate identities')
    return set(d['topologies']), {'status':'REFERENCE_ONLY_NO_MUTATION','sha256':digest(blob),'topology_set_sha256':digest(content),'active_count':len(d['topologies'])}


def select_b0(cfg:dict, mode:str)->list[float]:
    if mode == 'pilot':return [float(x) for x in cfg['pilot_B0']]
    f=cfg['fine_B0_range']
    # Avoid floating point creep in the last element.
    k=int(round((f['max']-f['min'])/f['step']))
    return [round(f['min']+i*f['step'],9) for i in range(k+1)]


def build(cfg:dict, out:Path, mode:str='pilot', baseline:Path|None=None, dry_run:bool=False)->dict:
    active,base_info=read_active_baseline(baseline)
    bvals=select_b0(cfg,mode)
    families=cfg['families']
    seen=set()
    for f in families:
        pair=(f['p'],f['q'])
        if pair in seen:raise ValueError('duplicate p,q pair')
        seen.add(pair)
        for b in bvals:validate_torus(f['p'],f['q'],b,cfg['geometry_R0'],cfg['point_count'])
    summary={'mode':mode,'family_count':len(families),'shape_count':len(families)*len(bvals),
             'B0_values':bvals,'Lambda_values':cfg['Lambda'],'baseline':base_info,
             'scientific_status':'INITIAL_GEOMETRY_ONLY_DYNAMICS_NOT_RUN',
             'active_v034_topology_set_modified':False,
             'source_independent_provider_count':1,
             'filaments_per_configuration':1, 'perturbed_child_geometries':len(families)*len(bvals)}
    if dry_run:return summary
    if out.exists():raise FileExistsError(f'output already exists; refusing overwrite: {out}')
    out.mkdir(parents=True)
    index=[]; scenarios=[]; comp_rows=[]; sha_records=[]
    for f in families:
        p,q=f['p'],f['q']
        ident=f'T_{p}_{q}'
        for b in bvals:
            stem=f'{ident}_B{int(round(b*10000)):04d}_N{cfg["point_count"]}'
            pts=sample_ruban(p,q,b,cfg['point_count'],cfg['geometry_R0'],cfg['theta0'])
            raw=coordinates_bytes(pts)
            outpath=out/'seeds'/ident/(stem+'.xyz')
            outpath.parent.mkdir(parents=True,exist_ok=True)
            outpath.write_bytes(raw)
            pert=ruban_inspired_perturbation(pts,p,q)
            pertpath=out/'seeds_perturbed'/ident/(stem+'_eps01.xyz')
            pertpath.parent.mkdir(parents=True,exist_ok=True)
            pertraw=coordinates_bytes(pert)
            pertpath.write_bytes(pertraw)
            m=geometric_diagnostics(pts)
            # Exact analytic closure by sin/cos periodicity and gcd(p,q)=1; numerical seam is sampled edge, not gap.
            m['analytic_continuum_closure']='PASS'
            m['closed_polygon_edge_norm_R0']=float(np.linalg.norm(pts[0]-pts[-1]))
            rec={
                'seed_id':stem,'topology_id':f['topology_id'],'parametric_embedding':ident,
                'is_member_of_active_v034':(None if active is None else f['topology_id'] in active),
                'xyz_path':outpath.relative_to(out).as_posix(),'sha256':digest(raw),
                'perturbed_xyz_path':pertpath.relative_to(out).as_posix(),
                'perturbed_sha256':digest(pertraw),
                'perturbation':{'method':'RUBAN_INSPIRED_DETERMINISTIC_NOT_FIGURE_REPRODUCTION',
                    'x_multiplier':1.01,'y_multiplier':1/1.01,
                    'even_q_z_multiplier':'1+0.005*sin(p*beta)' if q%2==0 else '1',
                    'topology_of_sampled_perturbation':'UNVERIFIED'},
                'n_vortex_filaments':1,'p':p,'q':q,'B0':b,'R0':cfg['geometry_R0'],
                'minor_radius_over_R0':b,'theta0':cfg['theta0'],
                'regularization_core_width_over_R0':None,
                'provenance_group':cfg['source_independence_group'],
                'embedding_group':f'ruban_T_{p}_{q}',
                'source_class':'ANALYTIC_PARAMETRIC_DERIVED_NOT_INDEPENDENT',
                'publication_claim_for_pair':f['literature_class'],
                'published_figure':f['figure'],
                'published_window_boundaries':'NOT_DIGITIZED',
                'geometry_metrics':m,
                'status':'RESEARCH_SEED_NOT_PASSED_PKLSA_ADMISSION_OR_DYNAMICS'}
            index.append(rec)
            comp_rows.append({'seed_id':stem,'topology_id':f['topology_id'] or '',
                'embedding':ident,'B0':b,'length_over_R0':m['length_over_R0'],
                'ideal_reference_ropelength':'', 'measured_ropelength':'',
                'max_survival_time':'','relative_equilibrium_residual':'','comparison_status':'NOT_EVALUATED'})
            for lam in cfg['Lambda']:
                for delt in cfg['delta_over_R0']:
                    scenarios.append({'seed_id':stem,'B0':b,'Lambda':lam,
                        'xi_over_R0':round(math.exp(-float(lam)),14),
                        'r0_over_xi':round(b*math.exp(float(lam)),9),
                        'slender_core_review':('REVIEW_R0_MINOR_NOT_MUCH_LARGER_THAN_XI' if b*math.exp(float(lam)) < 4.0 else 'NOT_EVALUATED'),
                        'slenderness_rule_provenance':'HEURISTIC_4X_REVIEW_ONLY_NOT_RUBAN_CRITERION',
                        'delta_over_R0':delt,'gamma_dimensionless':2*math.pi,
                        'dynamics_backend':'REQUIRES_INDEPENDENT_VALIDATED_SOLVER',
                        'recommended_initial_condition':pertpath.relative_to(out).as_posix(),
                        'dynamics_status':'NOT_RUN',
                        'survival_T':'NOT_MEASURED',
                        'gate':'PENDING'})
    if len({r['seed_id'] for r in index})!=len(index):raise AssertionError('duplicate seed id')
    write_json(out/'FAMILY_INDEX.json',{'schema':'E010-RUBAN-FAMILY-INDEX-1','family_slug':cfg['family_slug'],
        'status':'RESEARCH_ONLY_NOT_ADMITTED','source_contract_sha256':digest(CONFIG_PATH.read_bytes()),
        'baseline':base_info,'seed_count':len(index),'perturbed_child_count':len(index),'independent_source_count':1,
        'explain':'Parameter grid contains many geometry samples but represents one analytical data source. This is NOT 2 independent PKLSA carriers.',
        'seeds':index})
    write_json(out/'DYNAMICS_PENDING.json',{'status':'NOT_RUN','run_count':len(scenarios),
        'note':'Grid configurations are merely proposed; no stability-window locations or survival times are calculated.',
        'scenarios':scenarios})
    write_json(out/'BUILD_SUMMARY.json',summary)
    with (out/'GEOMETRY_VS_SURVIVAL.csv').open('w',newline='',encoding='utf-8') as fh:
        w=csv.DictWriter(fh,fieldnames=list(comp_rows[0]));w.writeheader();w.writerows(comp_rows)
    shalines=[]
    for p in sorted(out.rglob('*')):
        if p.is_file():shalines.append(f'{digest(p.read_bytes())}  {p.relative_to(out).as_posix()}')
    (out/'MANIFEST_SHA256.txt').write_text('\n'.join(shalines)+'\n',encoding='utf-8')
    return summary


def package(out:Path, zip_path:Path) -> None:
    if zip_path.exists():raise FileExistsError(f'archive already exists: {zip_path}')
    with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=f'{out.name}/{p.relative_to(out).as_posix()}')
    (zip_path.parent/(zip_path.name+'.sha256')).write_text(f'{digest(zip_path.read_bytes())}  {zip_path.name}\n',encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=['pilot','fine'],default='pilot')
    p.add_argument('--base-view',type=Path,help='Optional existing E010 v0.3.4 multiseed view directory or ZIP (read-only)')
    p.add_argument('--output-root',type=Path,help='Output folder; defaults to sibling of version directory')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--archive',action='store_true')
    args=p.parse_args()
    cfg=json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
    dest=(args.output_root or (PACKAGE_DIR.parent / OUT_NAME)).resolve()
    summary=build(cfg,dest,args.mode,args.base_view,args.dry_run)
    print(json.dumps(summary,indent=2))
    if args.archive and not args.dry_run:
        archive=dest.parent/ARCHIVE_NAME
        package(dest,archive)
        print(f'Packed: {archive}')


if __name__=='__main__':main()
