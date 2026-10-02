"""Append-only run identity, blind contamination checks and closed inventory seals.

Hashes provide tamper evidence relative to the retained commitment, not external
timestamping or protection against an adversary rewriting every commitment.
"""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import hashlib
import io
import json
import re
import secrets
import zipfile
import numpy as np

FALSIFIER = 'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier'
SEAL_NAME = 'BLIND_SEAL_SHA256.json'
_VALUES = tuple(Decimal(x) for x in ('1.09384563e6', '1.40897017e-15', '3.8934358266918687e18', '7.0e-7'))
_KEYS = {'vswirl', 'vswirlms', 'rc', 'rcm', 'rhocore', 'rhocorekgm3', 'rhof', 'rhofkgm3', 'gammac', 'gammacm2s', 'betac', 'betacm2s', 'tc', 'tcs', 'omegac', 'omegacs1'}
_NUMBER = re.compile(r'(?<![\w.])[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?(?![\w.])')


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def source_manifest(root):
    root = Path(root)
    allowed = {'.py', '.cpp', '.md', '.json', '.cmd', '.toml', '.txt', '.pyd', '.so'}
    return {p.relative_to(root).as_posix(): sha256_file(p)
            for p in sorted(root.rglob('*')) if p.is_file()
            and p.suffix.lower() in allowed
            and not any(part in {'build', '__pycache__', '.pytest_cache', '.git'} or part.endswith('.egg-info') for part in p.relative_to(root).parts)
            and p.name not in {'MANIFEST_SHA256.txt', '.a048_private_reveal.json'}}


def _forbidden_scalar(value):
    if isinstance(value, bool) or value is None:
        return False
    try:
        number = Decimal(str(value).strip())
    except InvalidOperation:
        return False
    return number.is_finite() and any(abs(number - ref) <= abs(ref) * Decimal('2e-15') for ref in _VALUES)


def _inspect(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if re.sub(r'[^a-z0-9]', '', str(key).lower()) in _KEYS:
                raise ValueError('canonical constant key in blind payload')
            _inspect(str(key))
            _inspect(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _inspect(item)
    elif isinstance(value, str):
        # Whole digests are opaque commitments, never numerical evidence.
        if re.fullmatch(r'[0-9a-fA-F]{64}', value):
            return
        if _forbidden_scalar(value) or any(_forbidden_scalar(m.group()) for m in _NUMBER.finditer(value)):
            raise ValueError('canonical constant value in blind payload')
    elif _forbidden_scalar(value):
        raise ValueError('canonical constant value in blind payload')


def assert_blind_safe(value):
    _inspect(value)


def scan_blind(blind):
    """Inspect every final file, including nested JSON, CSV and NPZ arrays.

    Unsupported binary files fail closed. Error reports never reproduce forbidden
    values, so a scan diagnostic cannot itself leak the reveal-only constants.
    """
    files = [p for p in sorted(Path(blind).rglob('*')) if p.is_file()]
    for path in files:
        if path.is_symlink():
            raise ValueError('symlink in blind payload')
        suffix = path.suffix.lower()
        try:
            if suffix == '.json':
                _inspect(read_json(path))
            elif suffix == '.jsonl':
                for line in path.read_text(encoding='utf-8').splitlines():
                    if line.strip():
                        _inspect(json.loads(line))
            elif suffix == '.csv':
                with path.open(encoding='utf-8-sig', newline='') as stream:
                    for row in csv.DictReader(stream):
                        _inspect(row)
            elif suffix in {'.npz', '.npy'}:
                loaded = np.load(path, allow_pickle=False)
                arrays = {key: loaded[key] for key in loaded.files} if suffix == '.npz' else {'array': loaded}
                for key, arr in arrays.items():
                    _inspect({key: []})
                    if arr.dtype.kind in 'fiu':
                        for ref in _VALUES:
                            if np.any(np.isclose(arr, float(ref), atol=0, rtol=2e-15)):
                                raise ValueError('canonical constant value in blind array')
                    elif arr.dtype.kind == 'c':
                        for ref in _VALUES:
                            if np.any(np.isclose(arr.real, float(ref), atol=0, rtol=2e-15)) or np.any(np.isclose(arr.imag, float(ref), atol=0, rtol=2e-15)):
                                raise ValueError('canonical constant in complex array')
                    elif arr.dtype.kind in 'US':
                        _inspect(arr.tolist())
                    else:
                        raise ValueError('unsupported blind array dtype')
                if suffix == '.npz':
                    loaded.close()
            elif suffix in {'.txt', '.md', '.log'}:
                content = path.read_text(encoding='utf-8')
                for line in content.splitlines():
                    # Plaintext key=value or key: value metadata is inspected too.
                    match = re.match(r'\s*([A-Za-z_][A-Za-z0-9_-]*)\s*[:=]', line)
                    if match:
                        _inspect({match.group(1): []})
                _inspect(content)
            else:
                raise ValueError('unsupported blind file format')
        except (ValueError, UnicodeError) as exc:
            raise ValueError(f'blind payload rejected: {path.name} ({type(exc).__name__})') from None
    return {'status': 'PASS', 'scanned_file_count': len(files)}


def create_run(root, version, suite, config, output_parent=None):
    root = Path(root).resolve()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', suite):
        raise ValueError('suite must contain only letters, digits, underscore or hyphen')
    assert_blind_safe(config)
    parent = Path(output_parent) if output_parent else root.parent / f'{FALSIFIER}_v{version}-outputs'
    parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_id = f'{FALSIFIER}_v{version}_{suite}_{timestamp}_{secrets.token_hex(4)}'
    run = parent / run_id
    run.mkdir(exist_ok=False)
    for name in ('BLIND', 'REVEALED', 'PRIVATE'):
        (run / name).mkdir()
    write_json(run / 'RUN_IDENTITY.json', {'run_id': run_id, 'falsifier': FALSIFIER,
               'version': version, 'suite': suite, 'created_utc': timestamp, 'source_root': str(root)})
    write_json(run / 'BLIND' / 'frozen_config.json', config)
    write_json(run / 'BLIND' / 'source_manifest.json', source_manifest(root))
    return run


def load_config(run):
    run = Path(run)
    config = read_json(run / 'BLIND' / 'frozen_config.json')
    prep = run / 'BLIND' / 'prepare_manifest.json'
    if prep.exists() and sha256_file(run / 'BLIND' / 'frozen_config.json') != read_json(prep)['config_sha256']:
        raise RuntimeError('frozen configuration commitment mismatch')
    return config


def commit_preparation(run, key):
    run = Path(run)
    write_json(run / 'PRIVATE' / 'reveal_key.json', key)
    write_json(run / 'BLIND' / 'prepare_manifest.json', {
        'run_id': run.name, 'stage': 'prepared', 'blind': True,
        'config_sha256': sha256_file(run / 'BLIND' / 'frozen_config.json'),
        'private_key_sha256': sha256_file(run / 'PRIVATE' / 'reveal_key.json'),
        'source_manifest_sha256': sha256_file(run / 'BLIND' / 'source_manifest.json'),
        'scope': 'SYNTHETIC_INSTRUMENT_QUALIFICATION_ONLY'})


def assert_unsealed(run):
    if (Path(run) / 'BLIND' / SEAL_NAME).exists():
        raise RuntimeError('sealed run is immutable; create a new run')


def _verify_bindings(run, verify_source=True, require_private_key=True):
    prep = read_json(run / 'BLIND' / 'prepare_manifest.json')
    for rel, key in [('BLIND/frozen_config.json', 'config_sha256'),
                     ('PRIVATE/reveal_key.json', 'private_key_sha256'),
                     ('BLIND/source_manifest.json', 'source_manifest_sha256')]:
        if rel == 'PRIVATE/reveal_key.json':
            if not require_private_key:
                continue
            if not (run/rel).is_file():
                rel='REVEALED/reveal_key.json'
        if not (run / rel).is_file() or sha256_file(run / rel) != prep[key]:
            raise RuntimeError(f'preparation commitment mismatch: {rel}')
    if verify_source:
        root = read_json(run / 'RUN_IDENTITY.json')['source_root']
        if source_manifest(root) != read_json(run / 'BLIND' / 'source_manifest.json'):
            raise RuntimeError('source manifest mismatch')
    return prep


def _inventory(blind):
    return {p.relative_to(blind).as_posix(): sha256_file(p) for p in sorted(blind.rglob('*'))
            if p.is_file() and p.relative_to(blind).as_posix() != SEAL_NAME}


def seal_run(run):
    run = Path(run)
    assert_unsealed(run)
    prep = _verify_bindings(run)
    scan = scan_blind(run / 'BLIND')
    seal = {'schema': 'A048_CLOSED_INVENTORY_SEAL_1', 'run_id': run.name,
            'inventory': _inventory(run / 'BLIND'), 'commitments': prep,
            'final_contamination_scan': scan}
    write_json(run / 'BLIND' / SEAL_NAME, seal)
    write_json(run / 'SEAL_COMMITMENT.json', {'run_id': run.name,
               'seal_sha256': sha256_file(run / 'BLIND' / SEAL_NAME),
               'identity_sha256': sha256_file(run / 'RUN_IDENTITY.json')})
    return seal


def verify_seal(run, verify_source=False, require_private_key=True):
    run = Path(run)
    commitment = read_json(run / 'SEAL_COMMITMENT.json')
    if commitment['seal_sha256'] != sha256_file(run / 'BLIND' / SEAL_NAME):
        raise RuntimeError('seal commitment mismatch')
    if commitment['identity_sha256'] != sha256_file(run / 'RUN_IDENTITY.json'):
        raise RuntimeError('run identity commitment mismatch')
    seal = read_json(run / 'BLIND' / SEAL_NAME)
    if seal['inventory'] != _inventory(run / 'BLIND'):
        raise RuntimeError('closed blind inventory mismatch: added, removed or modified file')
    if seal['commitments'] != _verify_bindings(run, verify_source=verify_source, require_private_key=require_private_key):
        raise RuntimeError('preparation/seal commitment mismatch')
    scan_blind(run / 'BLIND')
    return seal


def mark_revealed(run):
    run = Path(run)
    inventory = {p.relative_to(run / 'REVEALED').as_posix(): sha256_file(p)
                 for p in sorted((run / 'REVEALED').rglob('*')) if p.is_file()}
    write_json(run / 'REVEAL_COMMITMENT.json', {'inventory': inventory})


def verify_reveal(run):
    run = Path(run)
    inventory = {p.relative_to(run / 'REVEALED').as_posix(): sha256_file(p)
                 for p in sorted((run / 'REVEALED').rglob('*')) if p.is_file()}
    if read_json(run / 'REVEAL_COMMITMENT.json')['inventory'] != inventory:
        raise RuntimeError('revealed inventory mismatch')


def package_run(run):
    run = Path(run)
    verify_seal(run)
    verify_reveal(run)
    outputs = []
    for label, source in [('BLIND', run / 'BLIND'), ('REVEALED', run / 'REVEALED'), ('outputs', run)]:
        destination = run.parent / f'{run.name}_{label}.zip'
        with zipfile.ZipFile(destination, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(source.rglob('*')):
                if path.is_file() and 'PRIVATE' not in path.relative_to(source).parts:
                    archive.write(path, (Path(source.name) / path.relative_to(source)).as_posix())
            if label in {'BLIND','REVEALED'}:
                envelope=['RUN_IDENTITY.json', 'SEAL_COMMITMENT.json' if label=='BLIND' else 'REVEAL_COMMITMENT.json']
                for name in envelope:
                    archive.write(run/name,name)
        destination.with_suffix('.zip.sha256').write_text(sha256_file(destination) + '  ' + destination.name + '\n', encoding='utf-8')
        outputs.append(str(destination))
    return outputs
