from __future__ import annotations
import hashlib, json, platform, sys
from pathlib import Path
from datetime import datetime, timezone

FORBIDDEN_TARGET_KEYS={"h","hbar","planck","speed_of_light","c_m_s","alpha","fine_structure"}

def canonical_json(obj) -> str:
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True)

def sha256_bytes(b: bytes)->str: return hashlib.sha256(b).hexdigest()
def sha256_file(path: str|Path)->str:
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""): h.update(chunk)
    return h.hexdigest()

def audit_forbidden_targets(obj,where="config"):
    hits=[]
    def walk(x,path):
        if isinstance(x,dict):
            for k,v in x.items():
                kl=str(k).lower()
                if kl in FORBIDDEN_TARGET_KEYS or "planck" in kl: hits.append(path+"."+str(k))
                walk(v,path+"."+str(k))
        elif isinstance(x,list):
            for i,v in enumerate(x): walk(v,f"{path}[{i}]")
    walk(obj,where)
    if hits: raise RuntimeError("Blind protocol violation: forbidden target keys: "+", ".join(hits))

def source_hashes() -> dict[str,str]:
    root=Path(__file__).resolve().parents[1]
    files=[]
    files += sorted((root/"sst_einstein").rglob("*.py"))
    files += [root/"cpp"/"native.cpp",root/"setup.py",root/"requirements.txt"]
    out={}
    for p in files:
        if p.exists(): out[str(p.relative_to(root)).replace("\\","/")]=sha256_file(p)
    return out

def make_manifest(config: dict, config_path: Path, input_hashes: dict, version: str) -> dict:
    audit_forbidden_targets(config)
    src=source_hashes()
    frozen={"version":version,"config":config,"input_hashes":input_hashes,"source_hashes":src}
    protocol_hash=sha256_bytes(canonical_json(frozen).encode())
    return {
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "protocol_hash_sha256":protocol_hash,
        "config_path":str(config_path),
        "config_sha256":sha256_file(config_path),
        "input_hashes":input_hashes,
        "source_hashes":src,
        "package_version":version,
        "python":sys.version,
        "platform":platform.platform(),
        "blind_rule":"No h, hbar, c, alpha, or benchmark target for E/nu or sqrt(dE/dM) is loaded or compared during gate evaluation.",
        "threshold_rule":"Gate thresholds and source hashes are frozen before research outputs are produced.",
    }
