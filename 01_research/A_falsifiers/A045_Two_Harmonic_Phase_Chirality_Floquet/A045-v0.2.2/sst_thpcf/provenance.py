from __future__ import annotations
import hashlib, json, platform, sys, re
from pathlib import Path
import numpy as np

DENYLIST = {
    "alpha": r"(?<![A-Za-z0-9_])alpha(?![A-Za-z0-9_])",
    "v_circlearrow": r"v[_\\]?circlearrow",
    "gamma": r"(?<![A-Za-z0-9_])gamma(?![A-Za-z0-9_])",
    "circulation": r"(?<![A-Za-z0-9_])circulation(?![A-Za-z0-9_])",
    "rho_core": r"rho[_\\]?core",
    "rho_f": r"rho[_\\]?f(?![A-Za-z0-9_])",
    "r_c": r"(?<![A-Za-z0-9_])r_c(?![A-Za-z0-9_])",
}



def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def anon_id(record: dict, salt: str) -> str:
    h = hashlib.blake2b((salt+canonical_json(record)).encode(), digest_size=8).hexdigest()
    return "A"+h.upper()


def environment_manifest() -> dict:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": np.__version__,
    }


BLIND_SOURCE_GLOBS = (
    "configs/**/*.json",
    "cpp/**/*.c",
    "cpp/**/*.cc",
    "cpp/**/*.cpp",
    "cpp/**/*.cxx",
    "cpp/**/*.h",
    "cpp/**/*.hpp",
    "sst_thpcf/**/*.py",
    "data/FROZEN_INPUTS.json",
    "data/provenance/**/*.json",
)

# The audit implementation contains the denylist by definition.  It is not a
# scientific model/input module and must not audit its own token table.
BLIND_SOURCE_EXCLUDE_EXACT = {
    "sst_thpcf/provenance.py",
}


def _blind_source_surface(root: Path) -> list[tuple[str, Path]]:
    """Return the preregistered blind-source surface as normalized relative paths.

    Positive selection is intentional: build products, output/certification trees,
    reveal maps, caches, archives and other runtime artefacts can never enter G0.
    """
    root = Path(root).resolve()
    found: dict[str, Path] = {}
    for glob in BLIND_SOURCE_GLOBS:
        for p in root.glob(glob):
            if not p.is_file():
                continue
            rel = p.relative_to(root).as_posix()
            if rel in BLIND_SOURCE_EXCLUDE_EXACT:
                continue
            found[rel] = p
    return sorted(found.items())


def source_leakage_audit(root: Path) -> dict:
    """Fail-closed leakage audit over the blind scientific source/input surface.

    v0.2.1 recursively inspected nearly every file under ``root``.  On a local
    native run that allowed generated certification JSON and a compiler ``.obj``
    file to contaminate G0.  v0.2.2 audits only the preregistered text surface.
    """
    root = Path(root).resolve()
    surface = _blind_source_surface(root)
    hits = []
    read_errors = []
    scanned_files = []
    for rel, p in surface:
        try:
            txt = p.read_text(encoding="utf-8", errors="strict").lower()
        except Exception as exc:
            read_errors.append({"file": rel, "error": f"{type(exc).__name__}: {exc}"})
            continue
        scanned_files.append(rel)
        for tok, pattern in DENYLIST.items():
            if re.search(pattern, txt, flags=re.IGNORECASE):
                hits.append({"file": rel, "token": tok})
    surface_nonempty = bool(surface)
    passed = surface_nonempty and not read_errors and not hits
    return {
        "schema": "SST-THPCF-BLIND-SOURCE-AUDIT-2",
        "pass": passed,
        "policy": "positive_allowlist_fail_closed",
        "surface_nonempty": surface_nonempty,
        "n_surface_files": len(surface),
        "n_scanned": len(scanned_files),
        "source_globs": list(BLIND_SOURCE_GLOBS),
        "excluded_exact": sorted(BLIND_SOURCE_EXCLUDE_EXACT),
        "scanned_files": scanned_files,
        "read_errors": read_errors,
        "hits": hits,
        "denylist": list(DENYLIST),
    }
