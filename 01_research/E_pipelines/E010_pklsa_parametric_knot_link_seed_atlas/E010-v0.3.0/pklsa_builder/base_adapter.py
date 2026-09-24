from __future__ import annotations
from pathlib import Path
import json, numpy as np, sys

def _import_v020(base_root):
    root=Path(base_root)
    if str(root) not in sys.path: sys.path.insert(0,str(root))
    import pklsa
    return pklsa

def load_v020_carrier(base_root, carrier):
    sk=_import_v020(base_root)
    if carrier.representation=='pklsa_v020_compact':
        return sk.get_reference(carrier.reference_id,n=None,normalize_length=None)
    if carrier.representation=='pklsa_v020_candidate':
        _row,pts=sk.get(carrier.reference_id)
        return [np.asarray(x,float) for x in pts]
    raise ValueError(carrier.representation)
