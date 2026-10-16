"""Create instance-private commitments exactly once; never rotate secrets."""
from pathlib import Path
import secrets,json
ROOT=Path(__file__).resolve().parent
policy=json.loads((ROOT/'blind_policy.json').read_text())
paths=[ROOT/policy['private_nonce_path'],ROOT/'private/OPAQUE_ID_KEY.bin']
frozen=(ROOT/'preregistration/FROZEN_PROTOCOL.json').exists()
for p in paths:
    p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        if frozen or (ROOT/policy['commitment_path']).exists() or (ROOT/policy['reveal_commitment_path']).exists():
            raise SystemExit('FAIL CLOSED: private key absent but protocol/commitments already exist; restore the original private file')
        try:
            with p.open('xb') as f: f.write(secrets.token_bytes(32))
        except FileExistsError: pass
    if p.stat().st_size!=32: raise SystemExit('FAIL CLOSED: unexpected secret length '+str(p))
    print('Private materiaal aanwezig:',p.name,'| bytes:',p.stat().st_size)
