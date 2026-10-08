from __future__ import annotations
from pathlib import Path
import importlib, json, sys
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
