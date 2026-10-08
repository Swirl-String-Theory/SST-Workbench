from __future__ import annotations
from pathlib import Path
import atexit, importlib, importlib.util, json, os, shutil, sys, tempfile
from .util import read_json, sha256_file
from .workbench import a054_family

A054_REQUIRED=(
    'BLIND_MANIFEST.json','CERT_CONFIG.json','BACKEND_QUALIFICATION.json',
    'CERT_RESULTS_BLIND.json','CERT_ANALYSIS_BLIND.json','CERT_REPORT_BLIND.md','CERT_BLIND_SEAL.json'
)


def verify_a054_seal(campaign: Path) -> dict:
    c=Path(campaign); s=read_json(c/'CERT_BLIND_SEAL.json')
    checks={
      'manifest_sha256':'BLIND_MANIFEST.json','results_sha256':'CERT_RESULTS_BLIND.json',
      'analysis_sha256':'CERT_ANALYSIS_BLIND.json','report_sha256':'CERT_REPORT_BLIND.md',
      'config_sha256':'CERT_CONFIG.json','backend_qualification_sha256':'BACKEND_QUALIFICATION.json'}
    mismatches={}
    for key,name in checks.items():
        got=sha256_file(c/name); exp=s.get(key)
        if got!=exp: mismatches[name]={'expected':exp,'actual':got}
    priv=c/'_private'/'PRIVATE_MAPPING.json'
    if priv.is_file():
        got=sha256_file(priv); exp=s.get('private_mapping_commitment')
        if got!=exp: mismatches['_private/PRIVATE_MAPPING.json']={'expected':exp,'actual':got}
    if mismatches: raise RuntimeError(f'A054 seal mismatch: {mismatches}')
    return {'status':'PASS','schema':s.get('schema'),'campaign':str(c),'seal':s}


def _a054_campaign_ok(p:Path,preset='full'):
    if not p.is_dir() or not all((p/x).is_file() for x in A054_REQUIRED): return False
    try:
        m=read_json(p/'BLIND_MANIFEST.json')
        if m.get('preset')!=preset: return False
        verify_a054_seal(p); return True
    except Exception: return False


def find_a054_campaign(wb:Path,preset='full')->Path:
    root=a054_family(wb)
    hits=[p for p in root.rglob('*') if _a054_campaign_ok(p,preset)]
    if not hits:
        raise FileNotFoundError(
            f'No completed sealed A054 {preset} campaign found. A055 v0.4.0 never starts A054 automatically; '
            'finish/repair A054 first.')
    hits.sort(key=lambda p:(p.name,p.stat().st_mtime),reverse=True)
    return hits[0]


def verify_framework_output(out:Path,expected_mode='FULL')->dict:
    out=Path(out); mp=out/'OUTPUT_MANIFEST.json'; sp=out/'RUN_SUMMARY.json'
    if not mp.is_file() or not sp.is_file(): raise FileNotFoundError(f'framework output manifest/summary missing: {out}')
    man=read_json(mp); bad={}
    for row in man.get('files',[]):
        p=out/row['relpath']
        if not p.is_file(): bad[row['relpath']]={'expected':row['sha256'],'actual':'MISSING'}
        else:
            got=sha256_file(p)
            if got!=row['sha256']: bad[row['relpath']]={'expected':row['sha256'],'actual':got}
    summ=read_json(sp)
    if summ.get('mode')!=expected_mode: bad['mode']={'expected':expected_mode,'actual':summ.get('mode')}
    if bad: raise RuntimeError(f'framework upstream mismatch: {bad}')
    return {'status':'PASS','output':str(out),'protocol_bundle_sha256':summ.get('protocol_bundle_sha256'),'output_manifest_sha256':man.get('manifest_sha256')}


def _normalize_runner_rel(raw: str) -> str:
    return '/'.join(x for x in raw.replace('\\','/').split('/') if x)


def _read_runner_manifest(runner: Path) -> dict:
    mp=Path(runner)/'RUNNER_MANIFEST.json'
    if not mp.is_file():
        raise FileNotFoundError(f'A054 isolated runner manifest missing: {mp}')
    return read_json(mp)


def _verify_runner_manifest(runner: Path) -> dict:
    """Verify every RUNNER_MANIFEST tracked file byte-for-byte."""
    runner=Path(runner)
    m=_read_runner_manifest(runner)
    mismatches={}
    for raw,expected in (m.get('files') or {}).items():
        rel=_normalize_runner_rel(raw)
        p=runner/Path(*rel.split('/'))
        got=sha256_file(p) if p.is_file() else 'MISSING'
        if got!=expected:
            mismatches[rel]={'expected':expected,'actual':got}
    if mismatches:
        raise RuntimeError(f'A054 isolated runner manifest mismatch at {runner}: {mismatches}')
    return {'status':'PASS','runner':str(runner),'manifest':m,'tracked_file_count':len(m.get('files') or {})}


def _runner_manifest_native_expectation(runner:Path):
    m=_read_runner_manifest(runner); files=m.get('files',{})
    expected=None
    for key,value in files.items():
        if _normalize_runner_rel(key).casefold()=='a054_blind/_native.pyd':
            expected=value; break
    return {
        'manifest_present':True,
        'require_native':bool(m.get('require_native',False)),
        'require_openmp':bool(m.get('require_openmp',False)),
        'native_expected_sha256':expected,
        'python_version':m.get('python_version'),
        'native_import_verified_at_seal':m.get('native_import_verified'),
        'native_openmp_verified_at_seal':m.get('native_openmp_verified'),
    }


def _stage_a054_runner(source_runner: Path) -> dict:
    """Copy the sealed runner to a short temp path and re-verify it.

    A054 v0.2.0-r2 itself used a short temporary isolated-runner path during
    Windows native preflight.  Importing the same .pyd directly from the much
    deeper archived campaign path can hit WinError 206 (MAX_PATH) even though
    the binary hash is correct.  Staging changes no sealed bytes: both source
    and staged copy are verified against the same RUNNER_MANIFEST before use.
    """
    source_runner=Path(source_runner).resolve()
    source_verification=_verify_runner_manifest(source_runner)
    tmp_root=Path(tempfile.mkdtemp(prefix='a54_'))
    staged=tmp_root/'r'
    try:
        shutil.copytree(source_runner,staged)
        staged_verification=_verify_runner_manifest(staged)
    except Exception:
        shutil.rmtree(tmp_root,ignore_errors=True)
        raise
    # Keep the staging tree alive for the process lifetime.  Imported Python
    # modules and the native DLL may still refer to their load location.
    atexit.register(shutil.rmtree,tmp_root,ignore_errors=True)
    return {
        'source_runner':source_runner,
        'staged_runner':staged,
        'temp_root':tmp_root,
        'source_verification':source_verification,
        'staged_verification':staged_verification,
    }


def _clear_a054_namespace():
    for name in list(sys.modules):
        if name=='a054_blind' or name.startswith('a054_blind.'):
            del sys.modules[name]


def _ensure_a054_native(runner:Path) -> dict:
    """Load the hash-verified A054 native extension from a short staged path."""
    info=_runner_manifest_native_expectation(runner)
    pkgdir=runner/'a054_blind'
    candidates=sorted(pkgdir.glob('_native*.pyd'))
    if not candidates:
        if info['require_native']:
            raise RuntimeError(f'A054 sealed runner requires native backend but no _native*.pyd exists under {pkgdir}')
        return {**info,'status':'NOT_REQUIRED','path':None}
    pyd=candidates[0]
    got=sha256_file(pyd); exp=info.get('native_expected_sha256')
    if exp and got!=exp:
        raise RuntimeError(f'A054 isolated native hash mismatch: expected={exp}, actual={got}, path={pyd}')
    importlib.invalidate_caches()
    first_error=None
    try:
        mod=importlib.import_module('a054_blind._native')
        method='package_import'
    except Exception as exc:
        first_error=f'{type(exc).__name__}: {exc}'
        sys.modules.pop('a054_blind._native',None)
        dll_handles=[]
        if hasattr(os,'add_dll_directory'):
            for d in (pyd.parent,Path(sys.executable).resolve().parent):
                try: dll_handles.append(os.add_dll_directory(str(d)))
                except OSError: pass
        try:
            spec=importlib.util.spec_from_file_location('a054_blind._native',pyd)
            if spec is None or spec.loader is None:
                raise ImportError(f'no extension loader available for {pyd}')
            mod=importlib.util.module_from_spec(spec)
            sys.modules['a054_blind._native']=mod
            spec.loader.exec_module(mod)
            method='explicit_extension_loader'
        except Exception as exc:
            sys.modules.pop('a054_blind._native',None)
            raise RuntimeError(
                'A054 sealed native extension could not be loaded from short staging path; '
                f'path={pyd}; path_length={len(str(pyd))}; sha256={got}; first_import={first_error}; '
                f'explicit_import={type(exc).__name__}: {exc}; python={sys.version}'
            ) from exc
        finally:
            for h in dll_handles:
                try: h.close()
                except Exception: pass
    openmp=bool(getattr(mod,'openmp_enabled',False))
    if info.get('require_openmp') and not openmp:
        raise RuntimeError(f'A054 sealed runner requires OpenMP but loaded native reports openmp_enabled={openmp}: {pyd}')
    return {**info,'status':'PASS','path':str(pyd),'path_length':len(str(pyd)),'sha256':got,'load_method':method,'first_import_error':first_error,'openmp_enabled':openmp}


def import_a054_runner(campaign:Path):
    """Import a sealed A054 runner from a manifest-identical short staging copy."""
    source_runner=Path(campaign)/'blind_runner'
    if not (source_runner/'a054_blind'/'certify_v020.py').is_file():
        raise FileNotFoundError(f'A054 isolated blind runner absent: {source_runner}')

    stage=_stage_a054_runner(source_runner)
    runner=stage['staged_runner'].resolve()
    _clear_a054_namespace()
    r=str(runner)
    sys.path.insert(0,r)
    try:
        pkg=importlib.import_module('a054_blind')
        pkg_path=Path(pkg.__file__).resolve()
        if runner not in pkg_path.parents:
            raise RuntimeError(f'A054 package namespace collision: imported {pkg_path}, expected below {runner}')
        native_probe=_ensure_a054_native(runner)
        cert=importlib.import_module('a054_blind.certify_v020')
        geom=importlib.import_module('a054_blind.blind_geometry')
        phys=importlib.import_module('a054_blind.physics')
        modes=importlib.import_module('a054_blind.modes_v020')
        for mod in (cert,geom,phys,modes):
            mod_path=Path(mod.__file__).resolve()
            if runner not in mod_path.parents:
                raise RuntimeError(f'A054 module namespace collision: imported {mod_path}, expected below {runner}')
    except Exception:
        # Remove the staging path from sys.path if import fails. The atexit
        # cleanup remains harmless and preserves diagnostics until process exit.
        try: sys.path.remove(r)
        except ValueError: pass
        raise

    return {
        'runner': runner,
        'source_runner': source_runner.resolve(),
        'staging_root': stage['temp_root'],
        'source_manifest_verification': stage['source_verification'],
        'staged_manifest_verification': stage['staged_verification'],
        'certify': cert,
        'geometry': geom,
        'physics': phys,
        'modes': modes,
        'native_probe': native_probe,
    }
