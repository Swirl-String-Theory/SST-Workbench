from __future__ import annotations
import json
from pathlib import Path
import numpy as np


def load_npz(path: str | Path) -> tuple[dict[str, np.ndarray], dict]:
    path = Path(path)
    with np.load(path, allow_pickle=False) as z:
        arrays = {k: z[k] for k in z.files if k != "meta_json"}
        if "meta_json" not in z.files:
            raise ValueError(f"{path}: missing meta_json")
        raw = z["meta_json"]
        text = str(raw.item()) if raw.ndim == 0 else str(raw.reshape(-1)[0])
        meta = json.loads(text)
    return arrays, meta


def save_npz(path: str | Path, arrays: dict, meta: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(arrays)
    payload["meta_json"] = np.asarray(json.dumps(meta, sort_keys=True))
    np.savez_compressed(path, **payload)
