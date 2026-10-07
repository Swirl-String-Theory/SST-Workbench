from __future__ import annotations
from pathlib import Path
import argparse, shutil, hashlib, json, re, sys, subprocess, os


def sha(p: Path) -> str:
    h = hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()


def _copy_and_verify_native(dst: Path, pkg: Path, require_native: bool, require_openmp: bool):
    result = {
        'native_backend_copied': False,
        'native_import_verified': False,
        'native_openmp_verified': False,
        'native_source': None,
        'native_destination': None,
        'native_probe_file': None,
        'native_import_error': None,
    }
    try:
        import a054_ntaf._native as native
        src = Path(native.__file__).resolve()
        if not src.is_file():
            raise RuntimeError(f'native module file missing: {src}')
        result['native_source'] = str(src)
        ext = '.pyd' if os.name == 'nt' else '.so'
        copied = pkg / f'_native{ext}'
        shutil.copy2(src, copied)
        result['native_destination'] = str(copied)
        result['native_backend_copied'] = True

        code = (
            "import sys,json; "
            f"sys.path.insert(0,{str(dst)!r}); "
            "import a054_blind._native as n; "
            "print(json.dumps({'file':n.__file__,'openmp':bool(getattr(n,'openmp_enabled',False))}))"
        )
        probe = subprocess.run([sys.executable, '-c', code], text=True, capture_output=True)
        if probe.returncode != 0:
            raise RuntimeError((probe.stderr or probe.stdout).strip() or f'probe rc={probe.returncode}')
        payload = json.loads(probe.stdout.strip().splitlines()[-1])
        result['native_import_verified'] = True
        result['native_openmp_verified'] = bool(payload.get('openmp'))
        result['native_probe_file'] = payload.get('file')
        if require_openmp and not result['native_openmp_verified']:
            raise RuntimeError('isolated native backend imported but OpenMP is disabled')
    except Exception as e:
        result['native_import_error'] = repr(e)
        for candidate in (pkg / '_native.pyd', pkg / '_native.so'):
            candidate.unlink(missing_ok=True)
        result['native_backend_copied'] = False
        result['native_import_verified'] = False
        result['native_openmp_verified'] = False
        if require_native or require_openmp:
            raise RuntimeError('isolated native backend qualification failed: ' + repr(e)) from e
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--campaign', required=True)
    ap.add_argument('--require-native', action='store_true')
    ap.add_argument('--require-openmp', action='store_true')
    a = ap.parse_args()
    if a.require_openmp:
        a.require_native = True

    here = Path(__file__).resolve().parents[1]
    camp = Path(a.campaign)
    dst = camp / 'blind_runner'
    pkg = dst / 'a054_blind'
    if dst.exists():
        shutil.rmtree(dst)
    pkg.mkdir(parents=True)

    allow = ['blind_geometry.py', 'physics.py', 'seal.py', 'modes_v020.py', 'certify_v020.py']
    for name in allow:
        (pkg / name).write_text((here / 'src/a054_ntaf' / name).read_text(encoding='utf-8'), encoding='utf-8')
    (pkg / '__init__.py').write_text("__version__='0.2.0-r2-blind'\n", encoding='utf-8')

    native = _copy_and_verify_native(dst, pkg, a.require_native, a.require_openmp)

    run_cert = '''from pathlib import Path
import argparse, json
p=argparse.ArgumentParser(); p.add_argument('--campaign',required=True); p.add_argument('--config',required=True); a=p.parse_args()
cfg=json.loads(Path(a.config).read_text(encoding='utf-8'))
policy=cfg.get('backend_policy','prefer_native')
if policy in ('require_native','require_openmp'):
    try:
        from a054_blind import _native as n
    except Exception as e:
        raise RuntimeError('isolated runner cannot import native backend: '+repr(e)) from e
    if policy=='require_openmp' and not bool(getattr(n,'openmp_enabled',False)):
        raise RuntimeError('isolated runner native backend has OpenMP disabled: '+str(getattr(n,'__file__',None)))
    print('ISOLATED_NATIVE', {'file':str(getattr(n,'__file__',None)), 'openmp':bool(getattr(n,'openmp_enabled',False))})
from a054_blind.certify_v020 import run_certification
run_certification(Path(a.campaign),Path(a.config))
'''
    (dst / 'run_cert.py').write_text(run_cert, encoding='utf-8')

    forbidden_words = ['proton', 'neutron', 'borromean', 'triplegear', 'triple gear', 'uud', 'udd', 'twist-knot', 'preferred knot']
    forbidden_tokens = ['5_2', '6_1', 'P_A', 'P_B', 'P_C', 'N_A', 'N_B', 'N_C']
    leaked = []
    for p in dst.rglob('*.py'):
        src = p.read_text(encoding='utf-8'); low = src.lower()
        leaked += [(p.name, w) for w in forbidden_words if re.search(r'\b' + re.escape(w) + r'\b', low)]
        leaked += [(p.name, w) for w in forbidden_tokens if re.search(r'(?<![A-Za-z0-9_])' + re.escape(w) + r'(?![A-Za-z0-9_])', src)]
    if leaked:
        raise SystemExit(f'semantic leak in blind runner: {leaked}')

    files = sorted(p for p in dst.rglob('*') if p.is_file())
    manifest = {
        'schema': 'A054-ISOLATED-BLIND-RUNNER-2.1',
        'files': {str(p.relative_to(dst)): sha(p) for p in files},
        'semantic_leak_scan': 'PASS',
        'python_executable': sys.executable,
        'python_version': sys.version,
        'require_native': bool(a.require_native),
        'require_openmp': bool(a.require_openmp),
        **native,
    }
    (dst / 'RUNNER_MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
