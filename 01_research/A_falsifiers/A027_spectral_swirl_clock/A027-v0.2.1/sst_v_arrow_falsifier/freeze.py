from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
from .utils import sha256_file, save_json


def freeze(outdir):
    outdir=Path(outdir); target=outdir/"blind_results.json"
    if not target.exists(): raise FileNotFoundError(target)
    lock={"file":"blind_results.json","sha256":sha256_file(target),"frozen_utc":datetime.now(timezone.utc).isoformat(),"rule":"Unblind only after this hash is frozen."}
    save_json(outdir/"blind_lock.json",lock)
    return lock
