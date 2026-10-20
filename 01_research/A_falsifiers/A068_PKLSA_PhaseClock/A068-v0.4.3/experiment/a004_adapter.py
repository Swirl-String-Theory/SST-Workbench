"""A068 v0.4.3 immutable adapter to A004 historical geometry v0.2.2.

A004 is the SOLE owner of the 40 historical XYZ seeds. Nothing gets copied to
A068 science/data. A004 is a geometry seed library, not an independent physical
PKLSA dynamical provider. All inputs are byte-hash pinned before model execution.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np

VERSION='0.2.2'
LIBRARY_RELATIVE=Path('02_libraries/A_knot_libraries/A004_historical_trefoil/SST_Historical_Trefoil_XYZ_v0.2.2')
MANIFEST_SHA256='e7477a9c817f59124f279d08f001f5ef7f85c0a7c178e0ecf5b0b0116e57083e'
FAMILIES={'A':'A_Fourier_2015_p32','B':'B_Torus_2015_p66'}
RESOLUTIONS=(600,1200,2400,4800,9600)
CHIRALITIES=('orig','mirrorX')
TRAVERSALS=('ccw','cw')

class A004SourceError(RuntimeError):
    """Immutable source is missing, ambiguous or fails pinned provenance checks."""

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def workbench_from_instance(instance_root):
    p=Path(instance_root).resolve()
    if p.name!='A068-v0.4.3' or p.parent.name!='A068_PKLSA_PhaseClock' or p.parent.parent.name!='A_falsifiers' or p.parent.parent.parent.name!='01_research':
        raise A004SourceError('Expected canonical 01_research/A_falsifiers/A068_PKLSA_PhaseClock/A068-v0.4.3 instance; no source fallback')
    return p.parents[3]

def library_root(workbench_root):
    return (Path(workbench_root)/LIBRARY_RELATIVE).resolve()

def _validated_release_path(workbench_root):
    wb=Path(workbench_root).resolve()
    release=library_root(wb)
    allowed=(wb/'02_libraries'/'A_knot_libraries').resolve()
    if not release.is_relative_to(allowed):
        raise A004SourceError('A004 symlink resolves outside canonical library boundary')
    if not release.is_dir():
        alternate=wb/'02_libraries/A_knot_libraries/A004_historical_trefoiul'
        suffix=f' (possible misspelled folder {alternate})' if alternate.exists() else ''
        raise A004SourceError(f'Missing pinned A004 v0.2.2 release: {release}{suffix}')
    return release

def filename(model='B',chirality='orig',traversal='ccw',resolution=1200,version=VERSION):
    if version!=VERSION or model not in FAMILIES or chirality not in CHIRALITIES or traversal not in TRAVERSALS or type(resolution) is not int or resolution not in RESOLUTIONS:
        raise A004SourceError('Unregistered A004 seed selection/version; accepted A/B, orig/mirrorX, ccw/cw, N600/1200/2400/4800/9600, v0.2.2')
    return f'{FAMILIES[model]}_{chirality}_{traversal}_N{resolution}_arclength.xyz'

def audit_library(workbench_root,check_geometry=True):
    release=_validated_release_path(workbench_root)
    data=release/'data'
    manifest_path=data/'manifest.json'
    if not manifest_path.is_file() or sha256(manifest_path)!=MANIFEST_SHA256:
        raise A004SourceError('A004 manifest missing or not the pinned v0.2.2 SHA-256')
    man=json.loads(manifest_path.read_text(encoding='utf-8'))
    if (man.get('version')!=VERSION or man.get('classification')!='HISTORICAL_GEOMETRY_SEED'
       or man.get('physical_pklsa_dynamics_qualified') is not False):
        raise A004SourceError('A004 manifest schema/classification mismatch')
    file_records={fn:d for family in man['seeds'].values() for fn,d in family['files'].items()}
    registered={filename(model,ch,tr,n) for model in FAMILIES for ch in CHIRALITIES for tr in TRAVERSALS for n in RESOLUTIONS}
    if set(file_records)!=registered or len(file_records)!=40:
        raise A004SourceError('A004 manifest is not the complete pinned 40-file release')
    actual_files={p.name for p in data.glob('*.xyz') if p.is_file()}
    if actual_files!=registered:
        raise A004SourceError(f'A004 XYZ inventory mismatch: missing={sorted(registered-actual_files)}, extras={sorted(actual_files-registered)}')
    files={}
    for name in sorted(registered):
        p=data/name
        expected=file_records[name]['sha256']
        actual=sha256(p)
        if expected!=actual:
            raise A004SourceError(f'A004 XYZ SHA256 mismatch: {name}')
        files[name]=actual
    if check_geometry:
        for model in FAMILIES:
            for n in RESOLUTIONS:
                orig=np.loadtxt(data/filename(model,'orig','ccw',n))
                cw=np.loadtxt(data/filename(model,'orig','cw',n))
                mir=np.loadtxt(data/filename(model,'mirrorX','ccw',n))
                mircw=np.loadtxt(data/filename(model,'mirrorX','cw',n))
                if orig.shape!=(n,3) or not np.all(np.isfinite(orig)):
                    raise A004SourceError('Malformed original A004 XYZ coordinates')
                edges=np.linalg.norm(np.roll(orig,-1,axis=0)-orig,axis=1)
                if np.min(edges)<=0 or np.std(edges)/np.mean(edges)>=.001:
                    raise A004SourceError('A004 XYZ is not a regular nondegenerate closed polygon')
                # v0.2.2 CW reversal holds starting vertex fixed.
                reversed_fixed=np.concatenate((orig[:1],orig[:0:-1]),axis=0)
                mirrored=orig.copy();mirrored[:,0]*=-1
                mirrored_reverse=np.concatenate((mirrored[:1],mirrored[:0:-1]),axis=0)
                if not (np.array_equal(cw,reversed_fixed) and np.array_equal(mir,mirrored) and np.array_equal(mircw,mirrored_reverse)):
                    raise A004SourceError(f'A004 chirality/traversal transform mismatch for {model} N{n}')
    return {'schema':'A068-A004-IMPORT-AUDIT-2','valid':True,'library_version':VERSION,
            'library_relative_path':LIBRARY_RELATIVE.as_posix(),
            'release_root':str(release),'manifest_sha256':MANIFEST_SHA256,
            'verified_xyz_sha256':files,'verified_files':len(files),
            'independent_physical_providers':0,'physical_clock':'UNRESOLVED',
            'source_type':'GEOMETRY_SEEDS_ONLY','symmetry_controls':'CW_FIRST_VERTEX_FIXED_MIRRORX',
            'geometry_validated':bool(check_geometry)}

def source_path(workbench_root,model='B',chirality='orig',traversal='ccw',resolution=1200,version=VERSION,verify=True):
    name=filename(model,chirality,traversal,resolution,version)
    release=_validated_release_path(workbench_root)
    p=release/'data'/name
    if verify:
        audit_library(workbench_root,check_geometry=True)
    return p

def load_seed(model='B',chirality='orig',traversal='ccw',resolution=1200,version=VERSION,*,workbench_root):
    """Return (N,3) array from a pinned A004 source, never re-generate or mutate."""
    return np.loadtxt(source_path(workbench_root,model,chirality,traversal,resolution,version,verify=True))
