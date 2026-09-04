from __future__ import annotations
import hashlib, json
from importlib import resources
from pathlib import Path


def source_catalog() -> dict:
    p=Path(str(resources.files('sst_knotlib.data').joinpath('source_catalog_v1.json')))
    raw=p.read_bytes(); h=hashlib.sha256(raw).hexdigest()
    hp=p.with_suffix('.sha256')
    expected=hp.read_text(encoding='ascii').split()[0].lower()
    if h.lower()!=expected:
        raise ValueError(f'source catalog SHA-256 mismatch: expected {expected}, got {h}')
    d=json.loads(raw.decode('utf-8')); d['_sha256']=h
    return d


def source_provider_info(source_family: str, source_path: str|None=None) -> dict:
    cat=source_catalog(); fam=(source_family or '').lower(); p=(source_path or '').lower()
    if fam=='ideal_gilbert_fourier': pid='gilbert_ideal'
    elif fam in {'fremlin_short_coordinate','fremlin_local'}: pid='fremlin_local_fourier'
    elif fam=='ridgerunner':
        pid='klotz_anderson_12crossing' if ('twelvedata' in p or '12cross' in p) else 'ridgerunner'
    elif fam.startswith('knotplot') or 'knotplot' in p: pid='knotplot'
    else: pid='internal' if fam in {'analytic','internal','generated'} else 'internal'
    rec=dict(cat['providers'][pid]); rec['provider_id']=pid; rec['catalog_id']=cat['catalog_id']; rec['catalog_sha256']=cat['_sha256']
    return rec
