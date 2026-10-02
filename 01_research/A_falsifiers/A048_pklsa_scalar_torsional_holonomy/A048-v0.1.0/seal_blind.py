from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parent
BLIND=ROOT.parent/'A048_PKLSA_Scalar_Torsional_Holonomy_Falsifier_v0.1.0-outputs'/'BLIND'
def digest(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
if __name__=='__main__':
    rows=[]
    for p in sorted(BLIND.rglob('*')):
        if p.is_file() and p.name!='BLIND_SEAL_SHA256.txt': rows.append(f'{digest(p)}  {p.relative_to(BLIND).as_posix()}')
    (BLIND/'BLIND_SEAL_SHA256.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(f'sealed {len(rows)} blind evidence files')
