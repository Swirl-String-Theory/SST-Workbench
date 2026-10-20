#!/usr/bin/env python3
"""Fail-closed adapter: SST Fourier Knot Seed Atlas v0.1.2 -> SST Knot Library.

Geometry-only integration. No independent topology, chirality, Euler or PKLSA certification.
Only NumPy required for audit; the frozen sst_knotlib dependency is required for prepare.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
from typing import Any

import numpy as np
from gates_g4_g5 import CANONICAL_RC_M, bind_physical_scale, independent_topology_screen, QualificationError
from g5_extended import extended_g5_screen

ADAPTER_VERSION = '0.2.6'
ADAPTER_ROOT = Path(__file__).resolve().parent
DEFAULT_ATLAS_ROOT = ADAPTER_ROOT.parent / 'A003-v0.1.2'
ATLAS_VERSION = 'v0.1.2'
PINNED_ATLAS_MANIFEST_SHA256 = '01d57ec3f259fee4a09caa6aac8d3410ad6e1d8a8f159c6a9fb7ba71d0a6169d'
PROFILES = {'BASIC': (1200, 2400), 'FULL': (4800, 9600)}
SAMPLINGS = ('uniform_t', 'uniform_s_polyline')
TORUS = {'3_1':(2,3),'5_1':(2,5),'7_1':(2,7),'8_19':(3,4),
         '9_1':(2,9),'10_124':(3,5),'T_3_7':(3,7),'T_4_5':(4,5),'T_3_8':(3,8)}
TWIST = {1:'3_1',2:'4_1',3:'5_2',4:'6_1',5:'7_2',6:'8_1',7:'9_2',8:'10_1',9:'twist_11cross'}
# Registry topology reference coverage in the Drive-reviewed SST Knot Library v0.2.5.
KATLAS_025 = {'3_1', '4_1', '6_2', '7_4'}

class GateFailure(RuntimeError):
    pass


def resolve_atlas_root(cli_atlas: Path | str | None = None, *, environ: dict[str, str] | None = None,
                       adapter_root: Path | None = None) -> Path:
    """Resolve the A003 atlas, without silently falling back from explicit overrides.

    Priority: command-line --atlas/--atlas-root, SST_ATLAS_ROOT, adjacent A003-v0.1.2.
    All variants require manifest.json and the full pinned audit still runs afterward.
    """
    env = os.environ if environ is None else environ
    root = ADAPTER_ROOT if adapter_root is None else Path(adapter_root)
    value = cli_atlas if cli_atlas is not None else env.get('SST_ATLAS_ROOT')
    atlas = Path(value).expanduser() if value else root.parent / 'A003-v0.1.2'
    atlas = atlas.resolve()
    if not (atlas / 'manifest.json').is_file():
        raise GateFailure(f'Atlas manifest.json ontbreekt: {atlas}. '
                          'Gebruik --atlas "<pad naar A003-v0.1.2>".')
    return atlas


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for buf in iter(lambda: f.read(1024*1024), b''):
            h.update(buf)
    return h.hexdigest()


def safe_atlas_file(root: Path, relative: str) -> Path:
    if not isinstance(relative,str) or not relative.startswith('xyz/') or not relative.endswith('.xyz'):
        raise GateFailure(f'unsafe or non-XYZ atlas path: {relative!r}')
    resolved=(root / relative).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise GateFailure(f'path escape or symlink: {relative}')
    if not resolved.is_file():
        raise GateFailure(f'file not found: {relative}')
    return resolved


def expected_catalog():
    d={}
    for knot,(p,q) in TORUS.items():
        for variant in ('direct','hoste'):
            d[f'torus_{knot}_{variant}']={'knot':knot,'family':'torus','p':p,'q':q,
                       'variant':{'direct':'direct_torus','hoste':'hoste_minimal'}[variant]}
    d['kauffman_3_1']={'knot':'3_1','family':'twist','m':1,'variant':'kauffman_1997'}
    d['kauffman_4_1']={'knot':'4_1','family':'twist','m':2,'variant':'kauffman_1997'}
    for m,knot in TWIST.items():
        if m==1:continue
        if m%2==0 or m%4==1:
            d[f'twist_{knot}_m{m}_boocher']={'knot':knot,'family':'twist','m':m,'variant':'boocher'}
        if m%4 in (0,3):
            d[f'twist_{knot}_m{m}_lissajous']={'knot':knot,'family':'twist','m':m,'variant':'hoste_zirbel'}
    fib={3:(2,3,5),4:(3,5,8),5:(5,8,13),6:(8,13,21),
         7:(13,21,34),8:(21,34,55)}
    controls={3:(2,5),4:(3,4),5:(5,9),6:(8,15),7:(13,22),8:(21,32)}
    for n,(p,q,k) in fib.items():
        d[f'fibonacci_F{n}']={'knot':'3_1' if n==3 else f'F({n})_UNCLASSIFIED',
            'family':'fibonacci_fourier','fibonacci_index':n,'mode_x':p,
            'mode_y':q,'mode_z':k,'variant':'kauffman_section6',
            'topology_claim':'TREFOIL_SOURCE' if n==3 else 'UNCLASSIFIED_BY_ROLFSEN'}
        d[f'fibonacci_torus_F{n}']={'knot':f'T({p},{q})',
            'family':'fibonacci_torus','fibonacci_index':n,
            'p':p,'q':q,'variant':'kauffman_section7',
            'topology_claim':'MATHEMATICAL_TORUS_CONSTRUCTION'}
        cp,cq=controls[n]
        d[f'nonfibonacci_torus_control_F{n}']={'knot':f'T({cp},{cq})',
            'family':'torus_control','control_for_fibonacci_index':n,
            'p':cp,'q':cq,'variant':'nonfibonacci_kauffman_section7',
            'topology_claim':'MATHEMATICAL_TORUS_CONSTRUCTION',
            'control_limitation':'NOT_TOPOLOGY_MATCHED'}
    return d


def load_manifest(root: Path) -> tuple[dict,Path]:
    path=(root/'manifest.json').resolve()
    if not path.is_file(): raise GateFailure('manifest.json missing')
    manifest=json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('version') != ATLAS_VERSION: raise GateFailure('unexpected atlas version')
    if manifest.get('status') != 'GEOMETRIC_SEEDS_ONLY': raise GateFailure('unexpected scientific status')
    if manifest.get('units') != 'dimensionless coordinate units': raise GateFailure('unrecognized atlas units')
    if manifest.get('profiles') != {k:list(v) for k,v in PROFILES.items()}:
        raise GateFailure('BASIC/FULL resolution profiles differ')
    if not isinstance(manifest.get('records'),list): raise GateFailure('missing records list')
    return manifest,path


def read_xyz(path:Path, n:int) -> np.ndarray:
    try: xyz=np.loadtxt(path,dtype=np.float64)
    except Exception as e: raise GateFailure(f'invalid XYZ: {path.name}: {e}') from e
    if xyz.shape != (n,3): raise GateFailure(f'bad XYZ shape: {path.name}: {xyz.shape} not {(n,3)}')
    if not np.isfinite(xyz).all(): raise GateFailure(f'NaN or inf: {path.name}')
    v=np.diff(np.vstack((xyz,xyz[:1])),axis=0)
    if np.any(np.linalg.norm(v,axis=1)<1e-12):
        raise GateFailure(f'zero-length edge/duplicate periodic endpoint: {path.name}')
    return xyz


def polyline_length(x:np.ndarray) -> float:
    return float(np.linalg.norm(np.diff(np.vstack((x,x[:1])),axis=0),axis=1).sum())


def projection_diagram(xyz:np.ndarray, max_n:int=320) -> dict:
    """Generic oriented diagram diagnostic; NOT topological or chirality certification.

    Projection is to fixed e1/e2 basis; pairwise segment intersection and depth
    determine the signed crossing sum. Reflection in the viewing plane must negate it.
    """
    v=xyz[::max(1,int(math.ceil(len(xyz)/max_n)))].astype(float)
    normal=np.array([0.37,0.61,0.70]);normal/=np.linalg.norm(normal)
    e1=np.cross(normal,[0.,0.,1.]);e1/=np.linalg.norm(e1)
    e2=np.cross(normal,e1)
    proj=np.column_stack((v@e1,v@e2));depth=v@normal
    a=proj; d=np.roll(a,-1,axis=0)-a; nz=np.roll(depth,-1)-depth
    n=len(v); signed=0; count=0; ambiguous=0
    for i in range(n):
        js=np.arange(i+2,n,dtype=int)
        if i==0: js=js[js != n-1]
        if not len(js): continue
        # 2D cross(d_i, d_j)
        den=d[i,0]*d[js,1]-d[i,1]*d[js,0]
        mask=np.abs(den)>1.e-12
        js=js[mask];den=den[mask]
        if not len(js):continue
        diff=a[js]-a[i]
        u=(diff[:,0]*d[js,1]-diff[:,1]*d[js,0])/den
        w=(diff[:,0]*d[i,1]-diff[:,1]*d[i,0])/den
        good=(u>1e-9)&(u<1-1e-9)&(w>1e-9)&(w<1-1e-9)
        if not np.any(good): continue
        js=js[good];u=u[good];w=w[good];den=den[good]
        delta=(depth[i]+u*nz[i])-(depth[js]+w*nz[js])
        ambiguous+=int(np.count_nonzero(np.abs(delta)<1e-9))
        valid=np.abs(delta)>=1e-9
        signed+=int(np.sum(np.sign(den[valid]*delta[valid])))
        count+=int(np.count_nonzero(valid))
    return {'projection_crossings':count,'signed_crossing_sum':signed,
            'ambiguous_crossings':ambiguous,'n_diagram':n,
            'status':'PROJECTION_DIAGNOSTIC_ONLY'}


def validate_atlas(root:Path, *, diagram:bool=True)->tuple[dict,dict]:
    root=root.resolve();manifest,mpath=load_manifest(root)
    expected=expected_catalog(); indexing={}; perimeters={}; diagrams={}
    total_expected=len(expected)*sum(len(v) for v in PROFILES.values())*len(SAMPLINGS)
    arc_nonuniformity=[]
    if len(manifest['records'])!=total_expected:
        raise GateFailure(f'expected {total_expected} manifest rows, received {len(manifest["records"])}')
    by_seed={}
    for rec in manifest['records']:
        if not isinstance(rec,dict):raise GateFailure('record must be a JSON object')
        kid=rec.get('id');n=rec.get('points');sample=rec.get('sampling')
        if kid not in expected:raise GateFailure(f'unknown seed id: {kid!r}')
        for key,val in expected[kid].items():
            if rec.get(key)!=val:raise GateFailure(f'conflicting declared {key} for {kid}')
        if not isinstance(n,int) or n not in (1200,2400,4800,9600):raise GateFailure(f'invalid N {n}')
        if rec.get('profile') != ('BASIC' if n<=2400 else 'FULL'):
            raise GateFailure(f'profile-N mismatch: {kid} N={n}')
        if sample not in SAMPLINGS:raise GateFailure(f'unknown sampling {sample}')
        key=(kid,sample,n)
        if key in indexing:raise GateFailure(f'duplicate record: {key}')
        if rec.get('file')!=f'xyz/{kid}_{sample}_N{n}.xyz':
            raise GateFailure(f'filename/seed mismatch: {key}')
        filename=safe_atlas_file(root,rec['file'])
        if sha256_file(filename)!=rec.get('sha256'):raise GateFailure(f'SHA256 mismatch: {filename}')
        xyz=read_xyz(filename,n)
        length=polyline_length(xyz)
        if not np.isclose(length,float(rec['polyline_length_coordinate_units']),rtol=0.012,atol=1e-11):
            raise GateFailure(f'length/manifest disagreement: {key}')
        if sample=='uniform_t' and not np.isclose(length,float(rec['polyline_length_coordinate_units']),rtol=1e-11,atol=1e-9):
            raise GateFailure(f'uniform_t perimeter does not match manifest: {key}')
        if sample=='uniform_s_polyline':
            seg=np.linalg.norm(np.diff(np.vstack((xyz,xyz[:1])),axis=0),axis=1)
            chord_ratio=float(seg.max()/seg.min())
            if chord_ratio > 1.35:
                arc_nonuniformity.append({'id':kid,'N':n,'chord_max_min_ratio':chord_ratio,
                    'interpretation':'high-curvature polygon chord disparity; source was arclength-reparameterized, not chord-equalized'})
            if chord_ratio > 4.0:
                raise GateFailure(f'extreme arc-polyline chord nonuniformity: {key}')
        indexing[key]=dict(rec)
        perimeters[key]=length
        if diagram and n==1200 and sample=='uniform_t':
            diag=projection_diagram(xyz)
            if diag['projection_crossings']<1 or diag['ambiguous_crossings']>0:
                raise GateFailure(f'unclear low-resolution projection witness: {kid}, {diag}')
            # Independent regression of geometry/mirror transform (not knot classification):
            nv=np.array([.37,.61,.70]);nv/=np.linalg.norm(nv)
            reflected=xyz-2*np.outer(xyz@nv,nv)
            mir=projection_diagram(reflected)
            if mir['signed_crossing_sum'] != -diag['signed_crossing_sum'] or mir['projection_crossings']!=diag['projection_crossings']:
                raise GateFailure(f'mirror projection diagnostic inconsistent: {kid}')
            diagrams[kid]=diag
        by_seed.setdefault(kid,set()).add((sample,n))
    required={(s,n) for s in SAMPLINGS for n in (1200,2400,4800,9600)}
    if any(val!=required for val in by_seed.values()) or set(by_seed)!=set(expected):
        raise GateFailure('missing seed/sampling/resolution combinations')
    if sha256_file(mpath) != PINNED_ATLAS_MANIFEST_SHA256:
        raise GateFailure('manifest hash differs from pinned v0.1.1 source; do not silently rebaseline')
    # Compare same-parameter point correspondence and polyline convergence in all profiles.
    convergence=[]
    for seed in expected:
        for sample in SAMPLINGS:
            for low,high in ((1200,2400),(2400,4800),(4800,9600)):
                a=read_xyz(root/indexing[(seed,sample,low)]['file'],low)
                b=read_xyz(root/indexing[(seed,sample,high)]['file'],high)
                norm=float(np.sqrt(np.mean(np.sum((a-a.mean(axis=0))**2,axis=1))))
                rms=float(np.sqrt(np.mean(np.sum((a-b[::2])**2,axis=1))))/norm
                limit=1e-12 if sample=='uniform_t' else 0.002
                if rms>limit:raise GateFailure(f'resolution registration FAIL: {seed} {sample} {low}/{high}, rel RMS={rms}')
                La=perimeters[(seed,sample,low)];Lb=perimeters[(seed,sample,high)]
                rel_length=abs(Lb-La)/Lb
                # Parameterization-specific PL length bias can change; test the trend without asserting dynamics.
                if rel_length>0.01:
                    raise GateFailure(f'perimeter nonconvergence: {seed} {sample} {low}/{high}, rel={rel_length}')
                convergence.append({'id':seed,'sampling':sample,'low_N':low,'high_N':high,
                                    'phase_registered_relative_rms':rms,'perimeter_relative_delta':rel_length})
    reg={'schema':'sst.fourier-knot-atlas.external-registry/1',
         'adapter_version':ADAPTER_VERSION,'atlas_version':ATLAS_VERSION,
         'atlas_manifest_sha256':sha256_file(mpath),'atlas_units':'dimensionless coordinate units',
         'source_status':'GEOMETRIC_SEEDS_ONLY',
         'topology_verification':'NOT_INDEPENDENTLY_CERTIFIED',
         'chirality_verification':'NOT_INDEPENDENTLY_CERTIFIED',
         'records':[{**r,'expected_topology_source':'analytic construction / source manuscript',
                     'topology_status':'UNVERIFIED' if r['knot'] in KATLAS_025 else 'NOT_REGISTERED',
                     'chirality_status':'SOURCE_DECLARED_NOT_CERTIFIED',
                     'physical_scale_m_per_unit':None,
                     'measured_polyline_length_coordinate_units':
                     perimeters[(r['id'],r['sampling'],r['points'])]} for r in manifest['records']]}
    report={'adapter_version':ADAPTER_VERSION,'atlas_version':ATLAS_VERSION,'status':'GEOMETRIC_IMPORT_QUALIFIED',
            'source_records':len(indexing),'unique_seeds':len(expected),
            'manifest_sha256':sha256_file(mpath),'gate_results':{
                'G0_MANIFEST_SCHEMA':'PASS','G1_HASH_AND_XYZ':'PASS',
                'G2_GEOMETRIC_MIRROR_DIAGNOSTIC':'PASS' if diagram else 'NOT_RUN',
                'G3_SAMPLING_CONVERGENCE':'PASS','G4_PHYSICAL_SCALE':'NOT_DEFINED',
                'G5_INDEPENDENT_TOPOLOGY':'NOT_RUN','G6_PKLSA_EULER':'NOT_RUN'},
            'max_phase_registered_relative_rms':max(c['phase_registered_relative_rms'] for c in convergence),
            'max_relative_perimeter_delta':max(c['perimeter_relative_delta'] for c in convergence),
            'arclength_chord_warning_count':len(arc_nonuniformity),
            'arclength_chord_warnings':arc_nonuniformity,
            'crossing_diagnostics':diagrams,'convergence':convergence}
    return reg,report


def atomic_json(path:Path,obj:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    s=json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n'
    with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,delete=False,newline='\n') as f:
        f.write(s);tmp=f.name
    os.replace(tmp,path)


def require_knot_library(home:str|None,version:str):
    if home:
        loc=Path(home).resolve()
        if not loc.is_dir():raise GateFailure(f'SST_KNOT_LIBRARY_HOME not found: {loc}')
        sys.path.insert(0,str(loc))
    try:import sst_knotlib as sk
    except ImportError as e:raise GateFailure(f'sst_knotlib dependency missing; set SST_KNOT_LIBRARY_HOME: {e}') from e
    if str(sk.__version__)!=version:
        raise GateFailure(f'Knot Library version mismatch: expected {version}, actual {sk.__version__}')
    if home and not Path(sk.__file__).resolve().is_relative_to(Path(home).resolve()):
        raise GateFailure(f'Knot Library imported outside pinned root: {sk.__file__}')
    for attribute in ('load_geometry','prepare_for_falsifier'):
        if not hasattr(sk,attribute):raise GateFailure(f'Knot Library lacks {attribute}')
    return sk


def prepared_asset(root:Path, reg:dict, *, seed:str,sampling:str,n:int,
                   target_N:int,core_radius:float,unit_scale_m:float|None,
                   expected_library_version:str,knotlib_home:str|None,topology_provider:str,
                   require_topology_certified:bool,out:Path):
    if not np.isfinite(core_radius) or core_radius<=0:raise GateFailure('core-radius must be positive and finite')
    if unit_scale_m is not None and (not np.isfinite(unit_scale_m) or unit_scale_m<=0):
        raise GateFailure('unit-scale-m must be positive and finite')
    if target_N<32:raise GateFailure('target-N must be >= 32')
    selection=[r for r in reg['records'] if (r['id'],r['sampling'],r['points'])==(seed,sampling,n)]
    if len(selection)!=1:raise GateFailure('requested seed/sampling/N not found')
    r=selection[0]
    sk=require_knot_library(knotlib_home,expected_library_version)
    xyz=read_xyz(safe_atlas_file(root,r['file']),n)
    scale=1. if unit_scale_m is None else unit_scale_m
    # Use library's real file loader and confirm it did not reorder/modify points.
    loaded=sk.load_geometry(str(safe_atlas_file(root,r['file'])))
    libxyz=np.asarray(loaded.points,dtype=float)
    if libxyz.shape!=xyz.shape or not np.allclose(libxyz,xyz,rtol=0.,atol=0.):
        raise GateFailure('sst_knotlib.load_geometry changed source geometry')
    # 0.2.5 KAtlas has 4 pinned IDs. Other labels stay explicitly not registered.
    independent_expected=r['knot'] if r['knot'] in KATLAS_025 else None
    if require_topology_certified and independent_expected is None:
        raise GateFailure(f'cannot strict-certify {r["knot"]}: missing KAtlas v0.2.5 registry reference')
    result, lib_prov=sk.prepare_for_falsifier(
        xyz*scale,core_radius=float(core_radius),n=target_N,
        source_family='fourier_knot_seed_atlas',
        source_parameters={'atlas_version':ATLAS_VERSION,'id':seed,'sampling':sampling,
                           'origin_sha256':r['sha256'],'manifest_sha256':reg['atlas_manifest_sha256'],
                           'input_units':'m' if unit_scale_m is not None else 'dimensionless',
                           'unit_scale_m_per_coordinate_unit':unit_scale_m},
        expected_topology=independent_expected,topology_provider=topology_provider,
        require_topology_certified=require_topology_certified)
    result=np.asarray(result,dtype=np.float64)
    if result.shape!=(target_N,3) or not np.all(np.isfinite(result)):
        raise GateFailure('prepared output geometry failed finite/shape validation')
    if require_topology_certified and lib_prov.get('topology_certification',{}).get('status')!='CERTIFIED':
        raise GateFailure('Knot Library did not certify requested topology')
    if out.exists() or out.with_suffix('.json').exists():
        raise GateFailure('refusing to overwrite existing prepared asset')
    out.parent.mkdir(parents=True,exist_ok=True)
    metadata={'schema':'sst.fourier-atlas.prepared-seed/1','scientific_status':'GEOMETRIC_ONLY',
              'adapter_version':ADAPTER_VERSION,'atlas_manifest_sha256':reg['atlas_manifest_sha256'],
              'source_sha256':r['sha256'],'source_file':r['file'],'source_seed_id':seed,
              'source_expected_knot':r['knot'],'source_sampling':sampling,'source_n':n,
              'prepared_n':target_N,'coordinates_units':'m' if unit_scale_m is not None else 'dimensionless',
              'unit_scale_m_per_coordinate_unit':unit_scale_m,'core_radius_value':float(core_radius),
              'core_radius_units':'m' if unit_scale_m is not None else 'dimensionless coordinate units',
              'source_topology_status':r['topology_status'],
              'source_chirality_status':'SOURCE_DECLARED_NOT_CERTIFIED',
              'knot_library':lib_prov}
    # Write NPZ via tempfile: an in-progress failure must not leave a validated final artifact.
    with tempfile.NamedTemporaryFile(suffix='.npz',dir=out.parent,delete=False) as f:tmp=Path(f.name)
    try:
        np.savez_compressed(tmp,xyz=result)
        metadata['prepared_npz_sha256']=sha256_file(tmp)
        atomic_json(out.with_suffix('.json'),metadata)
        os.replace(tmp,out)
    finally:
        if tmp.exists():tmp.unlink()
    return metadata


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--atlas','--atlas-root',dest='atlas',type=Path,default=None,
                   help='Atlaspad; standaard: naast adapter in ../A003-v0.1.2 (of SST_ATLAS_ROOT)')
    p.add_argument('--out',type=Path,default=Path('outputs'))
    p.add_argument('--no-diagram',action='store_true',help='skip mirror/diagram check; G2 becomes NOT_RUN')
    p.add_argument('--reference-core-radius-units','--a-star',type=float,default=None,
                   help='G4 hypothesis: the specified radius in atlas units equals canonical r_c [m]')
    p.add_argument('--g5',action='store_true',help='G5 independent determinant screen via optional pyknotid')
    p.add_argument('--g5-extended',action='store_true',
                   help='bounded G5a-d: Alexander polynomial, signed v3, braid and projection/mesh witnesses')
    p.add_argument('--g5-extended-max-crossings',type=int,default=12,
                   help='predeclared symbolic provider limit; higher/unknown complexity is UNRESOLVED')
    p.add_argument('--require-g5-extended-complete',action='store_true',
                   help='fail closed if any selected seed is skipped, fails or remains unresolved')
    p.add_argument('--no-g5-projection-diagnostics',action='store_true',
                   help='do not compute extra predeclared projections after G5 failures')
    p.add_argument('--g5-sampling',choices=SAMPLINGS,default='uniform_t')
    p.add_argument('--g5-resolutions',choices=('BASIC','FULL','ALL'),default='BASIC')
    p.add_argument('--g5-family',choices=('ALL','torus','twist','fibonacci_fourier','fibonacci_torus','torus_control'),default='ALL',help='restrict optional numerical invariant screen to one declared family')
    p.add_argument('--require-g5-evidence',action='store_true',
                   help='fail closed unless invariant G5 screen completes without discrepancy')
    sp=p.add_subparsers(dest='command',required=True)
    sp.add_parser('audit',help='gate all 384 XYZ assets without modifying source atlas')
    sp.add_parser('catalog',help='emit read-only integration catalog and gate audit')
    pp=sp.add_parser('prepare',help='make frozen pre-PKLSA seed via installed SST Knot Library')
    pp.add_argument('--seed',required=True);pp.add_argument('--sampling',choices=SAMPLINGS,default='uniform_s_polyline')
    pp.add_argument('--N',type=int,choices=(1200,2400,4800,9600),default=2400)
    pp.add_argument('--target-N',type=int,default=512)
    pp.add_argument('--core-radius',type=float,required=True,help='in output coordinate units')
    pp.add_argument('--unit-scale-m',type=float,default=None,help='explicit physical-scale hypothesis (meters / source unit)')
    pp.add_argument('--knotlib-home',default=os.getenv('SST_KNOT_LIBRARY_HOME'))
    pp.add_argument('--expected-library-version',default='0.2.5')
    pp.add_argument('--topology-provider',default='auto')
    pp.add_argument('--require-topology-certified',action='store_true')
    args=p.parse_args(argv)
    try:
        atlas_root = resolve_atlas_root(args.atlas)
        registry,report=validate_atlas(atlas_root,diagram=not args.no_diagram)
        report['parent_release']='0.2.5'
        report['atlas_parent_release']='v0.1.1'
        report['source_atlas_unchanged']=True
        report['legacy_v0_1_1_sources_preserved']=True
        g4=bind_physical_scale(registry,report,
               assumed_core_radius_units=args.reference_core_radius_units)
        report['physical_scale_hypothesis']=g4
        resolution_lookup={'BASIC':(1200,2400),'FULL':(4800,9600),
                           'ALL':(1200,2400,4800,9600)}
        g5_registry = registry if args.g5_family == 'ALL' else {
            'records':[r for r in registry['records'] if r['family']==args.g5_family]}
        g5=independent_topology_screen(g5_registry,report,atlas_root=atlas_root,
                 enabled=args.g5,sample=args.g5_sampling,
                 n_values=resolution_lookup[args.g5_resolutions])
        g5['selected_family']=args.g5_family
        report['independent_topology_screen']=g5
        g5_extended = extended_g5_screen(g5_registry,report,atlas_root,
                enabled=args.g5_extended,sampling=args.g5_sampling,
                resolutions=resolution_lookup[args.g5_resolutions],
                max_crossings=args.g5_extended_max_crossings,
                projection_diagnostics=not args.no_g5_projection_diagnostics)
        report['extended_g5_screen']=g5_extended
        registry['physical_scale_hypothesis']=g4
        registry['independent_topology_screen']={key:value for key,value in g5.items() if key!='seed_results'}
        registry['extended_g5_screen']={key:value for key,value in g5_extended.items()
                                         if key not in ('seed_results','analytic_braid_references')}
        g5_extended_failed = (args.g5_extended and g5_extended['status'] in
                 ('PROVIDER_UNAVAILABLE','FAIL_INVARIANT_SCREEN')) or (
                 args.require_g5_extended_complete and
                 g5_extended['status']!='MULTI_INVARIANT_SCREEN_ONLY_NOT_CERTIFIED')
        g5_failed=(args.g5 and g5['status'] in ('PROVIDER_UNAVAILABLE',
                'FAIL_INVARIANT_SCREEN','PARTIAL_UNRESOLVED')) or (
                args.require_g5_evidence and g5['status']!='INVARIANT_SCREEN_ONLY_NOT_CERTIFIED')
        if args.command in ('audit','catalog'):
            atomic_json(args.out/'validation_report.json',report)
            if args.command=='catalog':
                atomic_json(args.out/'fourier_external_registry.json',registry)
            print(json.dumps({k:report[k] for k in ('status','source_records','unique_seeds','gate_results','max_phase_registered_relative_rms')},indent=2))
            if g5_failed or g5_extended_failed:
                print('FAIL_CLOSED: G5 partial, unavailable or contradictory; inspect validation_report.json',file=sys.stderr)
                return 2
        else:
            if g5_failed or g5_extended_failed:
                raise GateFailure('G5 partial, unavailable or contradictory')
            path=args.out/f'{args.seed}_{args.sampling}_N{args.N}_preparedN{args.target_N}.npz'
            if args.reference_core_radius_units is not None and args.unit_scale_m is not None:
                raise GateFailure('choose G4 reference radius OR --unit-scale-m, not both')
            scale=args.unit_scale_m if args.unit_scale_m is not None else g4.get('meters_per_atlas_unit')
            if args.reference_core_radius_units is not None and not math.isclose(
                      args.core_radius,CANONICAL_RC_M,rel_tol=1e-9):
                raise GateFailure('--core-radius must equal canonical r_c [m] with G4 anchored scale')
            meta=prepared_asset(atlas_root,registry,seed=args.seed,sampling=args.sampling,
                 n=args.N,target_N=args.target_N,core_radius=args.core_radius,
                 unit_scale_m=scale,expected_library_version=args.expected_library_version,
                 knotlib_home=args.knotlib_home,topology_provider=args.topology_provider,
                 require_topology_certified=args.require_topology_certified,out=path)
            atomic_json(args.out/'validation_report.json',report)
            print(json.dumps({'prepared':str(path),'scientific_status':meta['scientific_status']},indent=2))
        return 0
    except (GateFailure,QualificationError,ValueError,OSError,KeyError,ImportError) as e:
        print(f'FAIL_CLOSED: {e}',file=sys.stderr)
        return 2

if __name__=='__main__':sys.exit(main())
