from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, shutil, sys, time

CAMPAIGN_REL = Path('A054_Nucleon_Topology_Architecture_Blind_Falsifier_v0.2.0-outputs') / 'full_20261006_230912'
EXPECTED_NATIVE_SHA256 = 'ba6f8c9fdbcaa2525a4268d597c697c9067a331a170bd63a04b4440d640b2645'
PAYLOAD_NAME = '_native.pyd'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def normalize_manifest_key(k: str) -> str:
    return '/'.join(x for x in k.replace('\\', '/').split('/') if x)


def source_integrity(runner: Path, manifest: dict) -> tuple[dict, list[dict]]:
    checked = {}
    bad = []
    for raw, expected in (manifest.get('files') or {}).items():
        rel = normalize_manifest_key(raw)
        # pycache is runtime-derived; do not treat it as source authority.
        if '/__pycache__/' in f'/{rel}/' or rel.endswith('.pyc'):
            continue
        p = runner / Path(*rel.split('/'))
        actual = sha256_file(p) if p.is_file() else 'MISSING'
        checked[rel] = {'expected': expected, 'actual': actual, 'match': actual == expected}
        if actual != expected:
            bad.append({'path': rel, 'expected': expected, 'actual': actual})
    return checked, bad


def resolve_root(arg: str | None) -> Path:
    if arg:
        return Path(arg).resolve()
    here = Path(__file__).resolve().parent
    # If copied into A054-v0.2.0-r2, use that directory.
    if (here / CAMPAIGN_REL).is_dir():
        return here
    # Otherwise allow running directly from the repair kit by probing cwd.
    if (here.parent / CAMPAIGN_REL).is_dir():
        return here.parent
    cwd = Path.cwd().resolve()
    if (cwd / CAMPAIGN_REL).is_dir():
        return cwd
    if (cwd.parent / CAMPAIGN_REL).is_dir():
        return cwd.parent
    raise SystemExit(
        'Could not locate A054-v0.2.0-r2. Copy this repair kit into the A054-v0.2.0-r2 root '
        'or pass --a054-root <path>.'
    )


def main() -> int:
    ap = argparse.ArgumentParser(description='Restore the canonical A054 full_20261006_230912 native runner binary.')
    ap.add_argument('--a054-root', default=None)
    ap.add_argument('--verify-only', action='store_true')
    args = ap.parse_args()

    root = resolve_root(args.a054_root)
    campaign = root / CAMPAIGN_REL
    runner = campaign / 'blind_runner'
    pkg = runner / 'a054_blind'
    manifest_path = runner / 'RUNNER_MANIFEST.json'
    dest = pkg / '_native.pyd'
    payload = Path(__file__).resolve().parent / 'payload' / PAYLOAD_NAME

    if not manifest_path.is_file():
        raise SystemExit(f'Missing runner manifest: {manifest_path}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    files = manifest.get('files') or {}
    expected = None
    for k, v in files.items():
        if normalize_manifest_key(k).casefold() == 'a054_blind/_native.pyd':
            expected = v
            break
    if expected != EXPECTED_NATIVE_SHA256:
        raise SystemExit(f'Unexpected RUNNER_MANIFEST native hash: {expected!r}; expected canonical {EXPECTED_NATIVE_SHA256}')

    payload_hash = sha256_file(payload) if payload.is_file() else 'MISSING'
    if payload_hash != expected:
        raise SystemExit(f'Repair payload hash mismatch: {payload_hash}; expected {expected}')

    before_hash = sha256_file(dest) if dest.is_file() else 'MISSING'
    checked_before, bad_before = source_integrity(runner, manifest)
    non_native_bad_before = [x for x in bad_before if x['path'].casefold() != 'a054_blind/_native.pyd']
    if non_native_bad_before:
        raise SystemExit('Refusing native-only restore because other manifest-tracked source files differ: ' + json.dumps(non_native_bad_before, indent=2))

    report = {
        'schema': 'A054-NATIVE-RUNNER-RESTORE-1',
        'a054_root': str(root),
        'campaign': str(campaign),
        'runner_manifest': str(manifest_path),
        'expected_native_sha256': expected,
        'payload_sha256': payload_hash,
        'before_native_sha256': before_hash,
        'verify_only': bool(args.verify_only),
    }

    if args.verify_only:
        report['status'] = 'PASS' if before_hash == expected and not bad_before else 'FAIL'
        report['manifest_mismatches'] = bad_before
        print(json.dumps(report, indent=2))
        return 0 if report['status'] == 'PASS' else 1

    backup_path = None
    if before_hash != expected:
        backup_dir = root / 'A054-native-runner-backups'
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime('%Y%m%d_%H%M%S')
        backup_path = backup_dir / f'_native.before_restore_{stamp}_{str(before_hash)[:12]}.pyd'
        if dest.is_file():
            shutil.copy2(dest, backup_path)
        shutil.copy2(payload, dest)

    after_hash = sha256_file(dest) if dest.is_file() else 'MISSING'
    checked_after, bad_after = source_integrity(runner, manifest)
    report.update({
        'backup_path': None if backup_path is None else str(backup_path),
        'after_native_sha256': after_hash,
        'manifest_mismatches_after': bad_after,
        'status': 'PASS' if after_hash == expected and not bad_after else 'FAIL',
    })

    report_path = root / 'A054_native_runner_restore_report.json'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    print(f'Report: {report_path}')
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
