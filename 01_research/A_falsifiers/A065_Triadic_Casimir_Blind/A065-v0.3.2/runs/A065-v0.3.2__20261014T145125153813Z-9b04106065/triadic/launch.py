"""A065 v0.3.2: immutable-source, unique-run, create-only export orchestrator.

A fresh run receives a private snapshot of *unchanged scientific inputs*.
Neither the source tree nor any previous run is written by a new campaign.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIRS = ('data', 'seals', 'docs', 'triadic', 'framework_bridge', 'tests',
                 'tools', 'native', 'imports', 'preregistration')
SNAPSHOT_FILES = ('requirements.txt', 'README.md')
RUN_MODES = {'ALL', 'FRAMEWORK', 'FULL', 'BASIC', 'BLIND', 'REPORT', 'PARITY', 'DYNAMICS', 'QUALIFY'}
READ_MODES = {'VERIFY', 'SELFTEST', 'PROVIDER', 'PKLSA', 'CERTIFY', 'REVEAL'}


def _hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def _write_json_new(path: Path, document: object):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as fh:
        json.dump(document, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write('\n')


def _copy_new(src: Path, dst: Path) -> None:
    """Reject collisions, never copy2 onto existing evidence."""
    if not src.is_file():
        raise FileNotFoundError(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open('rb') as inp, dst.open('xb') as out:
        shutil.copyfileobj(inp, out)


def _new_run_dir():
    parent = ROOT / 'runs'
    parent.mkdir(parents=True, exist_ok=True)
    for _ in range(30):
        stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run_id = f'A065-v0.3.2__{stamp}-{secrets.token_hex(5)}'
        run = parent / run_id
        try:
            run.mkdir(mode=0o700, exist_ok=False)
            return run_id, run
        except FileExistsError:
            continue
    raise RuntimeError('Could not allocate a collision-free run directory')


def _snapshot(workspace: Path):
    def ignore(_folder, names):
        return [n for n in names if n in {'__pycache__', '.pytest_cache', '.venv', 'build', 'dist'} or n.endswith('.pyc')]
    for dirname in SNAPSHOT_DIRS:
        if (ROOT / dirname).is_dir():
            shutil.copytree(ROOT / dirname, workspace / dirname, ignore=ignore)
    for filename in SNAPSHOT_FILES:
        if (ROOT / filename).is_file():
            _copy_new(ROOT / filename, workspace / filename)


def _zip_new(dst: Path, entries: list[tuple[Path, str]]):
    """Create-only ZIP. The archive name encodes the run and source domain."""
    with zipfile.ZipFile(dst, mode='x', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for source, arcname in sorted(entries, key=lambda r: r[1]):
            z.write(source, arcname=arcname)


def _result_entries(workspace: Path):
    roots = ('outputs', 'seals', 'reports', 'FRAMEWORK_INSTANCE')
    return [
        (p, str(p.relative_to(workspace)).replace('\\', '/'))
        for d in roots if (workspace / d).is_dir()
        for p in (workspace / d).rglob('*')
        if p.is_file() and not any(x in ('private', 'private_reveal', 'revealed', 'REVEALED', '.venv', '__pycache__') for x in p.relative_to(workspace).parts)
        and p.suffix.lower() not in ('.pyd', '.dll', '.exe', '.pyc')
    ]


def _publish_exports(run_id: str, work: Path, export_dir: Path):
    report = work / 'reports' / f'{run_id}_FALSIFIER_REPORT.pdf'
    tex = work / 'reports' / f'{run_id}_FALSIFIER_REPORT.tex'
    for path in (report, tex):
        if path.is_file():
            _copy_new(path, export_dir / path.name)
    official = work / 'FRAMEWORK_INSTANCE' / 'A065-v0.3.2_FALSIFIER_REPORT.pdf'
    if official.is_file():
        _copy_new(official, export_dir / f'{run_id}_FRAMEWORK_FALSIFIER_REPORT.pdf')
    dynamics = work / 'outputs' / 'DYNAMICS_RESULT.json'
    if dynamics.is_file():
        _copy_new(dynamics, export_dir / f'{run_id}_DYNAMICS_RESULT.json')
    qualified = work / 'outputs' / 'QUALIFICATION_V032.json'
    if qualified.is_file():
        _copy_new(qualified, export_dir / f'{run_id}_QUALIFICATION_V032.json')
    entries = _result_entries(work)
    if entries:
        _zip_new(export_dir / f'{run_id}_BLIND_RESULTS.zip', entries)
    for ds in ('D01_EULER', 'D02_CLOCK_LINK', 'D03_TWO_SURFACE'):
        data_root = work / 'data' / ds
        if not data_root.is_dir():
            raise RuntimeError(f'missing dataset directory: {ds}')
        dataset_entries = [(p, str(p.relative_to(work)).replace('\\', '/')) for p in data_root.rglob('*') if p.is_file()]
        for name in (f'{ds}.seal.json', 'GLOBAL_COMMITMENT.json'):
            path = work / 'seals' / name
            if not path.is_file():
                raise RuntimeError(f'missing source commitment: {path}')
            dataset_entries.append((path, str(path.relative_to(work)).replace('\\', '/')))
        _zip_new(export_dir / f'{run_id}_{ds}_SEALED.zip', dataset_entries)
    hashes = {p.name: _hash(p) for p in export_dir.iterdir() if p.is_file()}
    _write_json_new(export_dir / f'{run_id}_EXPORT_SHA256.json', {
        'schema': 'A065-UNIQUE-EXPORTS-1', 'run_id': run_id,
        'policy': 'create-only; immutable previous runs; independent D01/D02/D03 source seals',
        'file_sha256': hashes,
    })


def _run_direct(args: list[str]) -> int:
    env = os.environ.copy()
    env['SST_A065_ISOLATED_RUN'] = '1'  # no project artefact writes in these modes
    cp = subprocess.run([sys.executable, '-m', 'triadic.entrypoint', *args], cwd=ROOT, env=env)
    return cp.returncode


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    mode = args[0].upper() if args else 'ALL'
    if mode == 'REVEAL':
        raise SystemExit('REVEAL_BLOCKED: v0.3.0 physical gates are open; do not reveal from a new run')
    if mode in READ_MODES:
        return _run_direct(args or [mode])
    if mode not in RUN_MODES:
        raise SystemExit(f'Unknown mode: {mode}. Use ALL FRAMEWORK BLIND REPORT PARITY DYNAMICS QUALIFY VERIFY SELFTEST PROVIDER PKLSA.')

    run_id, work = _new_run_dir()
    _snapshot(work)
    # Resolution is committed exactly once before both scientific/official runners.
    from .provider_manifest import write_new
    provider_record=write_new(work)
    export_dir = ROOT / 'exports' / run_id
    export_dir.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    env['SST_A065_ISOLATED_RUN'] = '1'
    env['SST_A065_RUN_ID'] = run_id
    env['SST_A065_EXPORT_DIR'] = str(export_dir)
    env['PYTHONDONTWRITEBYTECODE'] = '1'

    # REPORT regenerates the BLIND inputs as an independently sealed new campaign.
    actual_mode = 'BLIND' if mode == 'REPORT' else mode
    cmd = [sys.executable, '-m', 'triadic.entrypoint', actual_mode, *args[1:]]
    rc = 98
    try:
        proc = subprocess.run(cmd, cwd=work, env=env)
        rc = proc.returncode
    finally:
        # Metadata is written before the manifest, so its hash is included too.
        _write_json_new(export_dir / f'{run_id}_RUN_METADATA.json', {
            'schema': 'A065-RUN-ID-1', 'run_id': run_id,
            'requested_mode': mode, 'actual_mode': actual_mode,
            'returncode': rc, 'run_directory': str(work), 'exports': str(export_dir),
            'source_snapshot': 'A065-v0.3.2, three original seals unchanged',
            'provider_manifest_sha256':provider_record['manifest_sha256'],
        })
        _publish_exports(run_id, work, export_dir)
        print('\nRUN_ID:', run_id, '\nRUN_DIR:', work, '\nEXPORTS:', export_dir, flush=True)
    return rc


if __name__ == '__main__':
    raise SystemExit(main())
