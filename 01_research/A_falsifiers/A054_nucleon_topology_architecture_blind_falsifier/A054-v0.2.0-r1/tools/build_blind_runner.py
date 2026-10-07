from __future__ import annotations
from pathlib import Path
import argparse,shutil,hashlib,json,re,sys,subprocess,importlib.machinery

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--campaign',required=True); a=ap.parse_args()
    here=Path(__file__).resolve().parents[1]; camp=Path(a.campaign); dst=camp/'blind_runner'; pkg=dst/'a054_blind'
    if dst.exists(): shutil.rmtree(dst)
    pkg.mkdir(parents=True)
    allow=['blind_geometry.py','physics.py','seal.py','modes_v020.py','certify_v020.py']
    for name in allow: (pkg/name).write_text((here/'src/a054_ntaf'/name).read_text(encoding='utf-8'),encoding='utf-8')
    (pkg/'__init__.py').write_text("__version__='0.2.0-blind'\n",encoding='utf-8')
    native_copied=False
    native_import_verified=False
    native_import_error=None
    try:
        import importlib.util
        spec=importlib.util.find_spec('a054_ntaf._native')
        if spec and spec.origin:
            src=Path(spec.origin)
            # Refuse stale ABI binaries. The extension suffix must match THIS interpreter.
            if not any(src.name.endswith(suf) for suf in importlib.machinery.EXTENSION_SUFFIXES):
                raise RuntimeError(f'incompatible native extension for {sys.version}: {src.name}')
            copied=pkg/src.name
            shutil.copy2(src,copied); native_copied=True
            probe=subprocess.run(
                [sys.executable,'-c','import a054_blind._native as n; print(bool(getattr(n,\"openmp_enabled\",False)))'],
                cwd=str(dst), text=True, capture_output=True
            )
            if probe.returncode != 0:
                native_import_error=(probe.stderr or probe.stdout).strip()
                copied.unlink(missing_ok=True)
                native_copied=False
            else:
                native_import_verified=True
    except Exception as e:
        native_import_error=repr(e)
    (dst/'run_cert.py').write_text("from pathlib import Path\nimport argparse\nfrom a054_blind.certify_v020 import run_certification\np=argparse.ArgumentParser(); p.add_argument('--campaign',required=True); p.add_argument('--config',required=True); a=p.parse_args(); run_certification(Path(a.campaign),Path(a.config))\n",encoding='utf-8')
    forbidden_words=['proton','neutron','borromean','triplegear','triple gear','uud','udd','twist-knot','preferred knot']
    forbidden_tokens=['5_2','6_1','P_A','P_B','P_C','N_A','N_B','N_C']
    leaked=[]
    for p in dst.rglob('*.py'):
        src=p.read_text(encoding='utf-8'); low=src.lower()
        leaked += [(p.name,w) for w in forbidden_words if re.search(r'\b'+re.escape(w)+r'\b',low)]
        leaked += [(p.name,w) for w in forbidden_tokens if re.search(r'(?<![A-Za-z0-9_])'+re.escape(w)+r'(?![A-Za-z0-9_])',src)]
    if leaked: raise SystemExit(f'semantic leak in blind runner: {leaked}')
    files=sorted(p for p in dst.rglob('*') if p.is_file())
    manifest={'schema':'A054-ISOLATED-BLIND-RUNNER-2.0','files':{str(p.relative_to(dst)):sha(p) for p in files},'semantic_leak_scan':'PASS','native_backend_copied':native_copied,'native_import_verified':native_import_verified,'native_import_error':native_import_error,'python_executable':sys.executable,'python_version':sys.version}
    (dst/'RUNNER_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(dst)
if __name__=='__main__': main()
