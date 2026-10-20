"""Read the common per-run provider manifest; never perform independent fallback discovery."""
from __future__ import annotations
from pathlib import Path
from .provider_manifest import resolve,verify

def check(root,raw_override=None):
    root=Path(root)
    if raw_override is not None:
        return resolve(root,raw_override) # explicit interactive preview only; not framework evidence
    if (root/'outputs'/'PROVIDER_MANIFEST.json').is_file():
        return verify(root)
    # Read-only command before a campaign; this result has no run-level commitment.
    result=resolve(root)
    result['run_level_commitment']='NOT_FROZEN_PREVIEW'
    return result
