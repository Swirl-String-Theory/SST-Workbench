from __future__ import annotations
from pathlib import Path
import json
from .util import canonical_json_sha256, write_json

def load_config(path): return json.loads(Path(path).read_text(encoding="utf-8"))

def freeze_protocol(config:dict, out_path):
    payload={"schema":"SST-BLIND-PROTOCOL-1","protocol":config,"protocol_sha256":canonical_json_sha256(config)}
    write_json(out_path,payload); return payload

def verify_frozen(config:dict, frozen_path):
    p=json.loads(Path(frozen_path).read_text(encoding="utf-8"))
    return p.get("protocol_sha256")==canonical_json_sha256(config)
