"""A075 v0.2.0 pre-freeze private setup; supports safe partial recovery.
PRIVATE files never leave this workstation. Run preflight_contract.py first.
Does not change existing nonce, terms, or reveal. Never overwrites commitments.
"""
from __future__ import annotations
import hashlib,json,os,secrets,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PRIVATE=ROOT/'private'
PRE=ROOT/'preregistration'
FILES=("REVEAL_NONCE.bin","blind_forbidden_terms.txt","reveal.json")
COMMIT=("BLIND_TERMS_COMMITMENT.json","REVEAL_COMMITMENT.json")
KEY='OPAQUE_ID_KEY.bin'

def create_once(path:Path,data:bytes)->None:
    with path.open('xb') as fh: fh.write(data)
    try: path.chmod(0o600)
    except OSError: pass

def nonced_commit(domain:bytes,content:Path,nonce:Path)->str:
    return hashlib.sha256(domain+b'\0'+nonce.read_bytes()+b'\0'+content.read_bytes()).hexdigest()

def main()->int:
    if (PRE/'FROZEN_PROTOCOL.json').exists():
        print('REFUSED: protocol already frozen; no secret regeneration or modification permitted.')
        return 2
    existing_commit=[(PRE/f).exists() for f in COMMIT]
    existing_private=[(PRIVATE/f).exists() for f in FILES]
    if any(existing_commit):
        if not all(existing_commit) or not all(existing_private) or not (PRIVATE/KEY).is_file():
            print('REFUSED: existing commitments are incomplete; manual review required; no overwrite.')
            return 2
        nonce=PRIVATE/FILES[0]
        expected=[nonced_commit(b'SST-BLIND-TERMS-COMMIT-2',PRIVATE/FILES[1],nonce),
                  nonced_commit(b'SST-REVEAL-COMMIT-2',PRIVATE/FILES[2],nonce)]
        if any(json.loads((PRE/c).read_text(encoding='utf8')).get('sha256')!=v for c,v in zip(COMMIT,expected)):
            print('REFUSED: existing public/private commitments do not match!')
            return 2
        print('Already prepared and verified; existing private materials preserved.')
        return 0
    # A prior crashed run generated exactly these three files but no pre-reg dir.
    if any(existing_private) and not all(existing_private):
        print('REFUSED: only some original private files exist; do not silently regenerate secrets.')
        return 2
    if (PRIVATE/KEY).exists() and not all(existing_private):
        print('REFUSED: opaque key exists without a complete private set; inspect manually.')
        return 2
    # Never commit an invalid science contract. This check writes nothing.
    import subprocess
    rc=subprocess.call([sys.executable,str(ROOT/'tools'/'preflight_contract.py')],cwd=ROOT)
    if rc!=0:
        print('REFUSED: framework contract preflight failed; no blind commitments created.')
        return rc
    PRIVATE.mkdir(parents=True,exist_ok=True)
    PRE.mkdir(parents=True,exist_ok=True)
    if not all(existing_private):
        create_once(PRIVATE/FILES[0],secrets.token_bytes(32))
        create_once(PRIVATE/FILES[1],('A075_PRIVATE_HOLDOUT_'+secrets.token_hex(24)+'\n').encode('utf8'))
        create_once(PRIVATE/FILES[2],(json.dumps({
            'schema':'A075-PRIVATE-HOLDOUT-0.2.0',
            'nonce':secrets.token_hex(48),
            'secret_version':'A075-v0.2.0',
            'status':'NOT_REVEALED'
        },indent=2)+'\n').encode('utf8'))
    else:
        print('Recovering complete private nonce/terms/reveal from prior attempt; original bytes preserved.')
    if not (PRIVATE/KEY).exists():
        create_once(PRIVATE/KEY,secrets.token_bytes(32))
    nonce=PRIVATE/FILES[0]
    entries=[(COMMIT[0],{'schema':'SST-BLIND-TERMS-COMMITMENT-2',
        'sha256':nonced_commit(b'SST-BLIND-TERMS-COMMIT-2',PRIVATE/FILES[1],nonce),
        'terms_file_size':(PRIVATE/FILES[1]).stat().st_size}),
             (COMMIT[1],{'schema':'SST-REVEAL-COMMIT-2',
        'sha256':nonced_commit(b'SST-REVEAL-COMMIT-2',PRIVATE/FILES[2],nonce),
        'reveal_size':(PRIVATE/FILES[2]).stat().st_size})]
    # Use correct EXACT schema from Framework v1.0.10.
    entries[1][1]['schema']='SST-REVEAL-COMMITMENT-2'
    for filename,payload in entries:
        with (PRE/filename).open('x',encoding='utf8') as fh:
            json.dump(payload,fh,sort_keys=True,indent=2)
            fh.write('\n')
    print('PREPARED: exact framework SHA-256 nonced commitments and separate HMAC ID key.')
    print('Keep private/ OFF backups, SOURCE, BLIND and output ZIPs. Run run_all.cmd FREEZE next.')
    return 0
if __name__=='__main__': raise SystemExit(main())
