from __future__ import annotations
from pathlib import Path
import importlib, importlib.util, importlib.machinery, json, sys, os
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
            f'No completed sealed A054 {preset} campaign found. A055 v0.3.1 never starts A054 automatically; '
            'finish/repair A054 first.')
    hits.sort(key=lambda p:(p.name,p.stat().st_mtime),reverse=True)
    return hits[0]


def verify_a055_v030_output(out:Path)->dict:
    out=Path(out); seal_path=out/'BLIND'/'BLIND_SEAL.json'
    if not seal_path.is_file(): raise FileNotFoundError(f'A055 v0.3.0 BLIND seal missing: {seal_path}')
    seal=read_json(seal_path); bad={}
    for rel,h in seal.get('files',{}).items():
        p=out/'BLIND'/rel
        if not p.is_file(): bad[rel]={'expected':h,'actual':'MISSING'}
        else:
            got=sha256_file(p)
            if got!=h: bad[rel]={'expected':h,'actual':got}
    cfg=read_json(out/'BLIND'/'config_frozen.json')
    if cfg.get('campaign_id')!='A055-v0.3.0-full':
        bad['campaign_id']={'expected':'A055-v0.3.0-full','actual':cfg.get('campaign_id')}
    if bad: raise RuntimeError(f'A055 v0.3.0 seal/campaign mismatch: {bad}')
    return {'status':'PASS','manifest_sha256':seal.get('manifest_sha256'),'output':str(out)}


def import_a054_runner(campaign:Path):
    runner=Path(campaign)/'blind_runner'
    if not (runner/'a054_blind'/'certify_v020.py').is_file():
        raise FileNotFoundError(f'A054 isolated blind runner absent: {runner}')
    r=str(runner.resolve())
    if r not in sys.path: sys.path.insert(0,r)
    # If a stale module from another campaign was imported, fail rather than silently mix code.
    cert=importlib.import_module('a054_blind.certify_v020')
    geom=importlib.import_module('a054_blind.blind_geometry')
    # Load the same native artifact with a Windows extended path when the
    # isolated campaign layout exceeds the legacy DLL loader path limit.
    if os.name == 'nt' and 'a054_blind._native' not in sys.modules:
        native_dir = runner / 'a054_blind'
        for suffix in importlib.machinery.EXTENSION_SUFFIXES:
            artifact = native_dir / ('_native' + suffix)
            if artifact.is_file():
                spec = importlib.util.spec_from_file_location(
                    'a054_blind._native', '\\\\?\\' + str(artifact.resolve()))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules['a054_blind._native'] = module
                break
    phys=importlib.import_module('a054_blind.physics')
    modes=importlib.import_module('a054_blind.modes_v020')
    cert_path=Path(cert.__file__).resolve()
    if runner.resolve() not in cert_path.parents:
        raise RuntimeError(f'A054 module namespace collision: imported {cert_path}, expected below {runner.resolve()}')
    return {'runner':runner,'certify':cert,'geometry':geom,'physics':phys,'modes':modes}
