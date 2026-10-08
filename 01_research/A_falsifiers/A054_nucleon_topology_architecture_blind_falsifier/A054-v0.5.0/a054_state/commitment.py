from __future__ import annotations
from pathlib import Path
import argparse,hashlib,json,sys
COVERAGE=("experiment/**/*.py","a054_state/**/*.py","native_ext/*.cpp","native_ext/*.hpp","native_ext/*.py","configs/*.json","requirements.txt","tests/*.py","cross_falsifier_contract.json")
def compute_implementation_bundle(root):
    root=Path(root).resolve();files=[]
    for pat in COVERAGE:files.extend(p for p in root.glob(pat) if p.is_file())
    rows=[]
    for p in sorted(set(files)):rows.append({'path':p.relative_to(root).as_posix(),'size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    raw=(json.dumps({'files':rows},sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode('utf-8')
    return hashlib.sha256(raw).hexdigest(),rows
def expected_commitment(root):
    c=json.loads((Path(root)/'science_contract.json').read_text(encoding='utf-8'));return c.get('implementation_commitment',{}).get('bundle_sha256')
def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));ap.add_argument('--verify',action='store_true');a=ap.parse_args(argv)
    actual,rows=compute_implementation_bundle(a.root);expected=expected_commitment(a.root);ok=bool(expected) and actual==expected
    print(json.dumps({'schema':'A054-IMPLEMENTATION-VERIFICATION-1','expected':expected,'actual':actual,'ok':ok,'file_count':len(rows)},indent=2))
    return 0 if (ok or not a.verify) else 2
if __name__=='__main__':raise SystemExit(main())
