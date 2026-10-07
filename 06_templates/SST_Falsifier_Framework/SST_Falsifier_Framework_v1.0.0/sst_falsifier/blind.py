from __future__ import annotations
from pathlib import Path
import hashlib, hmac, json, os
from .util import write_json, read_json

DEFAULT_SUFFIXES=(".py",".json",".md",".txt",".toml",".cmd",".cpp",".h",".hpp",".tex",".csv")
PRIVATE_PARTS={"private","revealed","reveal_private"}

class BlindnessError(RuntimeError): pass


def load_forbidden_terms(path: str|Path) -> tuple[str,...]:
    terms=[]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        s=line.strip()
        if s and not s.startswith("#"): terms.append(s)
    return tuple(terms)


def scan_tree(root: str|Path, forbidden: tuple[str,...]|list[str], suffixes=DEFAULT_SUFFIXES):
    root=Path(root); hits=[]; terms=[t.casefold() for t in forbidden if t.strip()]
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suffixes: continue
        rel=p.relative_to(root)
        if any(part.casefold() in PRIVATE_PARTS for part in rel.parts): continue
        text=p.read_text(encoding="utf-8",errors="ignore").casefold()
        for term in terms:
            if term in text: hits.append({"path":rel.as_posix(),"term":term})
    return hits


def init_private_material(private_dir: str|Path, *, force: bool=False) -> dict:
    p=Path(private_dir); p.mkdir(parents=True,exist_ok=True)
    key=p/"OPAQUE_ID_KEY.bin"; nonce=p/"REVEAL_NONCE.bin"
    if force or not key.exists(): key.write_bytes(os.urandom(32))
    if force or not nonce.exists(): nonce.write_bytes(os.urandom(32))
    return {"key":str(key),"nonce":str(nonce)}


def opaque_id(seed: str, key: bytes, n: int=16) -> str:
    if len(key)<16: raise ValueError("opaque-ID HMAC key must be at least 128 bits")
    return hmac.new(key,seed.encode("utf-8"),hashlib.sha256).hexdigest()[:n].upper()


def _nonced_commitment(domain: bytes, payload_path: str|Path, nonce_path: str|Path) -> str:
    nonce=Path(nonce_path).read_bytes(); data=Path(payload_path).read_bytes()
    return hashlib.sha256(domain+b"\0"+nonce+b"\0"+data).hexdigest()


def blind_terms_commitment(terms_path: str|Path, nonce_path: str|Path, commitment_path: str|Path) -> dict:
    data=Path(terms_path).read_bytes(); digest=_nonced_commitment(b"SST-BLIND-TERMS-COMMIT-2",terms_path,nonce_path)
    payload={"schema":"SST-BLIND-TERMS-COMMITMENT-2","sha256":digest,"terms_file_size":len(data)}
    write_json(commitment_path,payload); return payload


def verify_blind_terms(terms_path: str|Path, nonce_path: str|Path, commitment_path: str|Path):
    expected=read_json(commitment_path)["sha256"]; actual=_nonced_commitment(b"SST-BLIND-TERMS-COMMIT-2",terms_path,nonce_path)
    return actual==expected,{"expected":expected,"actual":actual}


def assert_blind_tree(instance_root: str|Path):
    root=Path(instance_root); policy=read_json(root/"blind_policy.json")
    terms=root/policy["private_forbidden_terms_path"]; nonce=root/policy["private_nonce_path"]; commitment=root/policy["commitment_path"]
    ok,detail=verify_blind_terms(terms,nonce,commitment)
    if not ok: raise BlindnessError(f"private forbidden-term policy changed after commitment: {detail}")
    values=load_forbidden_terms(terms); hits=scan_tree(root,values)
    if hits: raise BlindnessError(f"blind contamination detected: {hits[:20]}")
    return {"forbidden_term_count":len(values),"hits":[],"commitment_sha256":read_json(commitment)["sha256"]}


def reveal_commitment(reveal_path: str|Path, nonce_path: str|Path, commitment_path: str|Path) -> dict:
    data=Path(reveal_path).read_bytes(); digest=_nonced_commitment(b"SST-REVEAL-COMMIT-2",reveal_path,nonce_path)
    payload={"schema":"SST-REVEAL-COMMITMENT-2","sha256":digest,"reveal_size":len(data)}
    write_json(commitment_path,payload); return payload


def verify_reveal(reveal_path: str|Path, nonce_path: str|Path, commitment_path: str|Path):
    expected=read_json(commitment_path)["sha256"]; actual=_nonced_commitment(b"SST-REVEAL-COMMIT-2",reveal_path,nonce_path)
    return actual==expected,{"expected":expected,"actual":actual}
