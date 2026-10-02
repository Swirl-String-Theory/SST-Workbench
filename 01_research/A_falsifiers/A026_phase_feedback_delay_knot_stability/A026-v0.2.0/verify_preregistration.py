from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parent
lock=json.loads((root/'PREREGISTRATION_LOCK.json').read_text(encoding='utf-8'))
ok=True
for rel,want in lock['sha256'].items():
    p=root/rel
    got=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    status='PASS' if got==want else 'FAIL'
    print(f'{status:4s} {rel}  {got}')
    ok &= got==want
print('PREREGISTRATION LOCK PASS' if ok else 'PREREGISTRATION LOCK FAIL')
raise SystemExit(0 if ok else 7)
