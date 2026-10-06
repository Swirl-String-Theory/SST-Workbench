from __future__ import annotations
from pathlib import Path
import argparse,shutil,hashlib,json

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--campaign',required=True); a=ap.parse_args()
    here=Path(__file__).resolve().parents[1]; camp=Path(a.campaign); dst=camp/'blind_runner'; pkg=dst/'a054_blind'
    if dst.exists(): shutil.rmtree(dst)
    pkg.mkdir(parents=True)
    allow=['blind.py','blind_geometry.py','physics.py','seal.py']
    for name in allow:
        text=(here/'src/a054_ntaf'/name).read_text(encoding='utf-8')
        # Relative imports remain valid under the isolated a054_blind package.
        (pkg/name).write_text(text,encoding='utf-8')
    (pkg/'__init__.py').write_text("__version__='0.1.1-blind'\n",encoding='utf-8')
    native_copied=False
    try:
        import importlib.util
        spec=importlib.util.find_spec('a054_ntaf._native')
        if spec and spec.origin:
            src=Path(spec.origin); shutil.copy2(src,pkg/src.name); native_copied=True
    except Exception:
        pass
    run='''from pathlib import Path\nimport argparse\nfrom a054_blind.blind import run_blind\np=argparse.ArgumentParser(); p.add_argument('--campaign',required=True); p.add_argument('--config',required=True); a=p.parse_args(); run_blind(Path(a.campaign),Path(a.config))\n'''
    (dst/'run_blind.py').write_text(run,encoding='utf-8')
    import re
    forbidden_words=['proton','neutron','borromean','triplegear','triple gear','uud','udd','twist-knot']
    forbidden_tokens=['5_2','6_1','P_A','P_B','P_C','N_A','N_B','N_C']
    leaked=[]
    for p in dst.rglob('*.py'):
        src=p.read_text(encoding='utf-8')
        low=src.lower()
        leaked += [(p.name,w) for w in forbidden_words if re.search(r'\b'+re.escape(w)+r'\b',low)]
        leaked += [(p.name,w) for w in forbidden_tokens if re.search(r'(?<![A-Za-z0-9_])'+re.escape(w)+r'(?![A-Za-z0-9_])',src)]
    if leaked: raise SystemExit(f'semantic leak in blind runner: {leaked}')
    files=sorted(p for p in dst.rglob('*') if p.is_file())
    manifest={'schema':'A054-ISOLATED-BLIND-RUNNER-1.1','files':{str(p.relative_to(dst)):sha(p) for p in files},'semantic_leak_scan':'PASS','native_backend_copied':native_copied}
    (dst/'RUNNER_MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(dst)
if __name__=='__main__': main()
