"""Pinned SST Knot Library dependency and portable KnotRecord bridge.

The falsifier does not vendor or silently install knot packages. A scientific run
must activate the exact first-party SST Knot Library release declared in config,
verify its release identity and manifest, and then bind source geometry to a
portable KnotRecord hash before scoring.
"""
from __future__ import annotations
from pathlib import Path
import hashlib, json, os, sys

_ACTIVE=None
_ACTIVE_MODULE=None


def _sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def _spec(cfg):
    s=dict(cfg.get('knot_library') or {})
    if not s:
        return {'required':False}
    s.setdefault('required',bool(cfg.get('require_knot_library_records',False)))
    s.setdefault('required_version','0.2.5')
    s.setdefault('relative_path','Knot_Library/SST_Knot_Library/SST_Knot_Library_v0.2.5')
    s.setdefault('env_var','SST_KNOT_LIBRARY_HOME')
    return s


def resolve_root(repo,cfg):
    spec=_spec(cfg)
    env=os.environ.get(spec.get('env_var','SST_KNOT_LIBRARY_HOME'),'').strip()
    root=Path(env) if env else Path(repo)/spec['relative_path']
    return root.resolve()


def activate(repo,cfg):
    """Activate and verify the exact configured SST Knot Library release."""
    global _ACTIVE,_ACTIVE_MODULE
    spec=_spec(cfg)
    if not spec.get('required') and not cfg.get('require_knot_library_records',False):
        return None
    root=resolve_root(repo,cfg)
    release_path=root/'RELEASE.json'; manifest_path=root/'MANIFEST_SHA256.txt'
    if not release_path.is_file(): raise FileNotFoundError(f'KNOT_LIBRARY_RELEASE_NOT_FOUND: {release_path}')
    if not manifest_path.is_file(): raise FileNotFoundError(f'KNOT_LIBRARY_MANIFEST_NOT_FOUND: {manifest_path}')
    release=json.loads(release_path.read_text(encoding='utf-8'))
    required=str(spec['required_version'])
    if str(release.get('version'))!=required:
        raise ValueError(f'KNOT_LIBRARY_RELEASE_VERSION_MISMATCH: expected {required}, got {release.get("version")}')
    # Refuse a stale sst_knotlib imported from another tree.
    existing=sys.modules.get('sst_knotlib')
    if existing is not None:
        loaded=Path(existing.__file__).resolve()
        try: loaded.relative_to(root)
        except ValueError: raise RuntimeError(f'KNOT_LIBRARY_ALREADY_IMPORTED_FROM_DIFFERENT_ROOT: {loaded}')
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    import sst_knotlib as sk
    if Path(sk.__file__).resolve().parent.parent != root:
        raise RuntimeError(f'KNOT_LIBRARY_IMPORT_ROOT_MISMATCH: {sk.__file__}')
    if str(sk.__version__)!=required:
        raise ValueError(f'KNOT_LIBRARY_RUNTIME_VERSION_MISMATCH: expected {required}, got {sk.__version__}')
    from sst_knotlib.integrity import verify_manifest
    from sst_knotlib.runtime import runtime_attestation
    integ=verify_manifest(root)
    if not integ.get('pass'): raise ValueError('KNOT_LIBRARY_MANIFEST_INTEGRITY_FAILED')
    runtime=runtime_attestation()
    if not runtime.get('release_identity',{}).get('match'): raise ValueError('KNOT_LIBRARY_RELEASE_IDENTITY_FAILED')
    reg=sk.KAtlasSnapshot(); cat=sk.source_catalog()
    att={
        'format':'SST-KNOT-LIBRARY-DEPENDENCY-1',
        'required_version':required,
        'runtime_version':str(sk.__version__),
        'release_sha256':_sha256(release_path),
        'manifest_sha256':_sha256(manifest_path),
        'manifest_file_count':int(integ.get('file_count',0)),
        'katlas_snapshot_id':reg.snapshot_id,
        'katlas_snapshot_sha256':reg.sha256,
        'source_catalog_id':cat['catalog_id'],
        'source_catalog_sha256':cat['_sha256'],
        'native_backend_imported':runtime.get('native_backend_imported'),
        'openmp_enabled':runtime.get('openmp_enabled'),
    }
    _ACTIVE=att; _ACTIVE_MODULE=sk
    return dict(att)


def current_attestation():
    return None if _ACTIVE is None else dict(_ACTIVE)


def module():
    if _ACTIVE_MODULE is None: raise RuntimeError('KNOT_LIBRARY_NOT_ACTIVATED')
    return _ACTIVE_MODULE


def _portable_record_dict(record, relative_path=None):
    d=record.to_dict() if hasattr(record,'to_dict') else json.loads(json.dumps(record))
    if relative_path is not None:
        d.setdefault('geometry',{})['source_path']=str(relative_path).replace('\\','/')
    return d


def _obj_sha(obj):
    raw=json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def make_source_record(path, *, expected='3_1', n=128, relative_path=None):
    sk=module()
    components,record=sk.make_knot_record(path,expected_topology=expected,n=int(n),
                                          topology_provider='reference-only',convergence_levels=(int(n),))
    if len(components)!=1: raise ValueError('KNOT_LIBRARY_SOURCE_NOT_SINGLE_COMPONENT')
    d=_portable_record_dict(record,relative_path)
    return components[0],d,_obj_sha(d)


def verify_source_record(path, entry, *, dataset_root, n=128):
    rel=Path(path).resolve().relative_to(Path(dataset_root).resolve()).as_posix()
    points,record,h=make_source_record(path,expected='3_1',n=int(entry.get('knot_record_resample_n',n)),relative_path=rel)
    expected=entry.get('knot_record_sha256')
    if not expected: raise ValueError('MISSING_KNOT_LIBRARY_RECORD_COMMITMENT')
    if h!=expected: raise ValueError('KNOT_LIBRARY_RECORD_COMMITMENT_MISMATCH')
    att=current_attestation() or {}
    if entry.get('knot_library_version')!=att.get('runtime_version'):
        raise ValueError('KNOT_LIBRARY_RECORD_VERSION_MISMATCH')
    if entry.get('katlas_snapshot_sha256')!=att.get('katlas_snapshot_sha256'):
        raise ValueError('KNOT_LIBRARY_KATLAS_SNAPSHOT_MISMATCH')
    if record.get('topology_expected')!='3_1' or record.get('geometry',{}).get('component_count')!=1:
        raise ValueError('KNOT_LIBRARY_RECORD_NOT_TREFOIL_SINGLE_COMPONENT')
    # Reference-only is intentionally not elevated to CERTIFIED.
    if record.get('topology_certification',{}).get('status') not in {'UNVERIFIED','CERTIFIED'}:
        raise ValueError('KNOT_LIBRARY_TOPOLOGY_RECORD_REJECTED')
    return points,record,h


def generate_braid_trefoil(n=512):
    sk=module(); p=sk.generate_topology_seed('3_1',method='braid',n=int(n))
    reg=sk.KAtlasSnapshot(); ref=reg.get('3_1').to_dict(); att=current_attestation() or {}
    rec={
        'topology_expected':'3_1','topology_reference':ref,
        'topology_certification':{'status':'UNVERIFIED','pass':False,'expected_topology':'3_1','provider':'reference-only',
                                  'notes':['constructive seed from pinned KAtlas braid reference; not external geometry certification']},
        'geometry':{'source_path':'GENERATED/KATLAS_BRAID_3_1','source_family':'sst_braid_closure','source_format':'generated_braid',
                    'component_count':1,'resample_N':int(n),'components':[{'N':len(p),'geometry_sha256':sk.geometry_sha256(p)}]},
        'provenance':{'knot_library':f'sst-knot-library/{att.get("runtime_version")}',
                      'katlas_snapshot_id':att.get('katlas_snapshot_id'),'katlas_snapshot_sha256':att.get('katlas_snapshot_sha256')}
    }
    return p,rec,_obj_sha(rec)


def main():
    import argparse
    from .io import load_json
    a=argparse.ArgumentParser(); a.add_argument('command',choices=['verify']); a.add_argument('--repo',required=True); a.add_argument('--config',required=True)
    args=a.parse_args(); cfg=load_json(args.config); print(json.dumps(activate(args.repo,cfg),indent=2))

if __name__=='__main__': main()
