from __future__ import annotations
from pathlib import Path
import importlib, json, os, shutil, sys, tempfile
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
            f'No completed sealed A054 {preset} campaign found. A055 v0.4.1 never starts A054 automatically; '
            'finish/repair A054 first.')
    hits.sort(key=lambda p:(p.name,p.stat().st_mtime),reverse=True)
    return hits[0]


def verify_framework_output(out:Path,expected_mode='FULL')->dict:
    out=Path(out); mp=out/'OUTPUT_MANIFEST.json'; sp=out/'RUN_SUMMARY.json'
    if not mp.is_file() or not sp.is_file(): raise FileNotFoundError(f'framework output manifest/summary missing: {out}')
    man=read_json(mp); bad={}
    rows=man.get('files',[])
    # Framework v1.0.6 self-hash contract when available; retain compatibility with v0.3.1's frozen v1.0.4 output.
    stored=man.get('manifest_sha256')
    if stored:
        import hashlib
        core=(json.dumps({'files':rows},sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
        calc=hashlib.sha256(core).hexdigest()
        if stored!=calc: bad['manifest_sha256']={'expected':stored,'actual':calc}
    for row in rows:
        rel=row.get('relpath') or row.get('path')
        if not rel: continue
        p=out/rel
        if not p.is_file(): bad[rel]={'expected':row.get('sha256'),'actual':'MISSING'}
        else:
            got=sha256_file(p)
            if got!=row.get('sha256'): bad[rel]={'expected':row.get('sha256'),'actual':got}
    summ=read_json(sp)
    if summ.get('mode')!=expected_mode: bad['mode']={'expected':expected_mode,'actual':summ.get('mode')}
    if bad: raise RuntimeError(f'framework upstream mismatch: {bad}')
    return {'status':'PASS','output':str(out),'protocol_bundle_sha256':summ.get('protocol_bundle_sha256'),'output_manifest_sha256':man.get('manifest_sha256')}


def _runner_rel(rel: str) -> Path:
    return Path(*rel.replace('\\','/').split('/'))


def _native_source_candidates(campaign:Path, manifest:dict, expected_hash:str):
    seen=set(); candidates=[]
    raw=manifest.get('native_source')
    if raw:
        p=Path(raw)
        candidates.append(p)
        # Re-anchor a stale absolute Windows provenance path inside the current A054 instance.
        name=Path(raw.replace('\\','/')).name
        inst=Path(campaign).parent.parent
        candidates.extend([inst/'src'/'a054_ntaf'/name, inst/'src'/name])
        try:
            candidates.extend(inst.rglob(name))
        except OSError:
            pass
    for p in candidates:
        key=os.path.normcase(str(p))
        if key in seen: continue
        seen.add(key)
        try:
            if p.is_file() and sha256_file(p)==expected_hash:
                yield p
        except OSError:
            continue


def prepare_a054_runner(campaign:Path):
    """Create an import-only mirror containing exactly the A054 runner manifest byte set.

    The upstream campaign is never mutated. Extra ABI-tagged extension files are deliberately
    omitted, eliminating Python extension-name precedence as a provenance ambiguity. If a
    manifest-listed native file is missing/corrupt, only an exact SHA-256 match to the recorded
    A054 native source may restore that single file. No numerically-similar rebuild is accepted.
    """
    campaign=Path(campaign); runner=campaign/'blind_runner'; mp=runner/'RUNNER_MANIFEST.json'
    if not (runner/'a054_blind'/'certify_v020.py').is_file():
        raise FileNotFoundError(f'A054 isolated blind runner absent: {runner}')
    if not mp.is_file(): raise FileNotFoundError(f'A054 RUNNER_MANIFEST.json absent: {mp}')
    manifest=read_json(mp); files=manifest.get('files')
    if not isinstance(files,dict) or not files: raise RuntimeError('A054 RUNNER_MANIFEST.json has no sealed files map')
    stage_root=Path(tempfile.mkdtemp(prefix='a055_v041_a054_runner_'))/'blind_runner'; stage_root.mkdir(parents=True)
    restored=[]; copied=[]; excluded=[]
    listed={_runner_rel(rel).as_posix() for rel in files}
    # Record but never copy executable extras. This is diagnostic, not an acceptance path.
    for p in runner.rglob('*'):
        if p.is_file():
            rel=p.relative_to(runner).as_posix()
            if rel not in listed and p.suffix.lower() in {'.pyd','.so','.dll'}:
                excluded.append({'relpath':rel,'sha256':sha256_file(p)})
    for rel,expected in sorted(files.items()):
        rp=_runner_rel(rel); src=runner/rp
        chosen=src if src.is_file() and sha256_file(src)==expected else None
        if chosen is None and rp.name.lower() in {'_native.pyd','_native.so'}:
            chosen=next(_native_source_candidates(campaign,manifest,expected),None)
            if chosen is not None:
                restored.append({'relpath':rp.as_posix(),'from':str(chosen),'sha256':expected})
        if chosen is None:
            actual='MISSING' if not src.is_file() else sha256_file(src)
            raise RuntimeError(f'A054 runner manifest mismatch: relpath={rp.as_posix()}, expected={expected}, actual={actual}')
        dst=stage_root/rp; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(chosen,dst)
        got=sha256_file(dst)
        if got!=expected: raise RuntimeError(f'A054 staged runner hash mismatch: relpath={rp.as_posix()}, expected={expected}, actual={got}')
        copied.append({'relpath':rp.as_posix(),'sha256':got})
    shutil.copy2(mp,stage_root/'RUNNER_MANIFEST.json')
    provenance={
      'schema':'A055-A054-RUNNER-IMPORT-PROVENANCE-041','status':'PASS',
      'source_runner':str(runner),'staged_runner':str(stage_root),
      'runner_manifest_sha256':sha256_file(mp),'manifest_file_count':len(files),
      'copied_file_count':len(copied),'restored_exact_native_files':restored,
      'excluded_unlisted_executables':excluded,
      'policy':'manifest_allowlist_exact_sha256_only_no_upstream_mutation'}
    return stage_root,provenance


def import_a054_runner(campaign:Path):
    runner,prov=prepare_a054_runner(campaign)
    # Prevent a prior campaign/module cache from deciding which extension Python resolves.
    for name in list(sys.modules):
        if name=='a054_blind' or name.startswith('a054_blind.'):
            del sys.modules[name]
    importlib.invalidate_caches()
    r=str(runner.resolve())
    if r not in sys.path: sys.path.insert(0,r)
    cert=importlib.import_module('a054_blind.certify_v020')
    geom=importlib.import_module('a054_blind.blind_geometry')
    phys=importlib.import_module('a054_blind.physics')
    modes=importlib.import_module('a054_blind.modes_v020')
    cert_path=Path(cert.__file__).resolve()
    if runner.resolve() not in cert_path.parents:
        raise RuntimeError(f'A054 module namespace collision: imported {cert_path}, expected below {runner.resolve()}')
    native_mod=getattr(phys,'_native_module',lambda:None)()
    native_path=None if native_mod is None else str(Path(native_mod.__file__).resolve())
    if native_path is not None and runner.resolve() not in Path(native_path).parents:
        raise RuntimeError(f'A054 native module namespace collision: imported {native_path}, expected below {runner.resolve()}')
    prov['imported_certify_path']=str(cert_path); prov['imported_native_path']=native_path
    if native_path:
        prov['imported_native_sha256']=sha256_file(native_path)
    return {'runner':runner,'certify':cert,'geometry':geom,'physics':phys,'modes':modes,'provenance':prov}
