#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ideal_source.py
===============
ONE place to resolve and load the David Fremlin ideal-knot database (ideal.txt,
the <AB>...</AB> format). Reuse this everywhere `ideal` is needed instead of each
script re-implementing its own path ladder / katlas download.

Resolution order (first hit wins):
  1. SSTcore bundled copy        ssc.get_ideal_txt_path() / parse_embedded_ideal_txt
  2. Env var                     $SST_IDEAL_TXT
  3. Local files                 ./ideal.txt, ./Ideal.txt, ./resources/(I)deal.txt, exports/
  4. GitHub (trusted repo)       raw .../Swirl-String-Theory/SSTcore/master/resources/ideal.txt
  5. katlas.org (gzip)           https://katlas.org/images/d/d2/Ideal.txt.gz

Downloads (4,5) are cached to a STABLE cache dir (NOT the current working dir,
fixing the cwd-pollution of the original generate_knot_fseries.prepare_database).

Parsing reuses ab_knot.py (single parser for the whole project).
"""
from __future__ import annotations
import os
import gzip
import urllib.request
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

try:
    import ab_knot
except ImportError:
    ab_knot = None  # parsing helpers degrade; path resolution still works

GITHUB_RAW = ("https://raw.githubusercontent.com/Swirl-String-Theory/"
              "SSTcore/master/resources/ideal.txt")
KATLAS_GZ = "https://katlas.org/images/d/d2/Ideal.txt.gz"
_MIN_BYTES = 100


def _cache_dir() -> Path:
    base = os.environ.get("SST_CACHE_DIR") or os.path.join(
        os.path.expanduser("~"), ".cache", "sst")
    d = Path(base)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ok(p: Optional[Path]) -> bool:
    try:
        return p is not None and p.is_file() and p.stat().st_size >= _MIN_BYTES
    except Exception:
        return False


def _sstcore_path() -> Optional[Path]:
    for name in ("SSTcore", "sstcore"):
        try:
            mod = __import__(name)
        except Exception:
            continue
        getter = getattr(mod, "get_ideal_txt_path", None)
        if getter:
            try:
                p = Path(getter())
                if _ok(p):
                    return p
            except Exception:
                pass
        rdir = getattr(mod, "get_resources_dir", None)
        if rdir:
            try:
                d = Path(rdir())
                for n in ("ideal.txt", "Ideal.txt"):
                    if _ok(d / n):
                        return d / n
            except Exception:
                pass
    return None


def _local_candidates() -> List[Path]:
    here = Path.cwd()
    out: List[Path] = []
    for d in (here, here / "resources", here / "exports"):
        for n in ("ideal.txt", "Ideal.txt"):
            out.append(d / n)
    return out


def _download(url: str, dest: Path, gz: bool = False) -> Optional[Path]:
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read()
        if gz:
            data = gzip.decompress(data)
        if len(data) < _MIN_BYTES:
            return None
        dest.write_bytes(data)
        return dest
    except Exception as e:
        print(f"[ideal_source] download failed ({url}): {e}")
        return None


def resolve_ideal_txt(allow_download: bool = True, force_refresh: bool = False) -> Path:
    """Return a usable path to ideal.txt, downloading to cache only if needed."""
    if not force_refresh:
        # 1) SSTcore bundled
        p = _sstcore_path()
        if p:
            return p
        # 2) env var
        env = os.environ.get("SST_IDEAL_TXT")
        if env and _ok(Path(env)):
            return Path(env)
        # 3) local files
        for c in _local_candidates():
            if _ok(c):
                return c
        # cached download from a previous run
        cached = _cache_dir() / "ideal.txt"
        if _ok(cached):
            return cached

    if not allow_download:
        raise FileNotFoundError("ideal.txt not found locally and downloads disabled")

    cached = _cache_dir() / "ideal.txt"
    # 4) GitHub (trusted: Swirl-String-Theory/SSTcore)
    got = _download(GITHUB_RAW, cached, gz=False)
    if _ok(got):
        return cached
    # 5) katlas.org gzip
    got = _download(KATLAS_GZ, cached, gz=True)
    if _ok(got):
        return cached
    raise FileNotFoundError("could not resolve ideal.txt from any source")


def load_ideal_text(allow_download: bool = True) -> str:
    return resolve_ideal_txt(allow_download=allow_download).read_text(
        encoding="utf-8", errors="ignore")


def parse_all(allow_download: bool = True
              ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """All <AB> blocks as (header, coeffs) via ab_knot (single project parser)."""
    if ab_knot is None:
        raise RuntimeError("ab_knot not importable; cannot parse ideal.txt")
    return ab_knot.parse_AB_blocks(load_ideal_text(allow_download))


def get_block_by_id(ab_id: str, allow_download: bool = True
                    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Return the (header, coeffs) for a given AB Id, e.g. '3:1:1'."""
    for header, coeffs in parse_all(allow_download):
        if str(header.get("Id", "")).strip() == ab_id:
            return header, coeffs
    raise KeyError(f"AB Id {ab_id!r} not found in ideal.txt")


if __name__ == "__main__":
    p = resolve_ideal_txt()
    print(f"resolved ideal.txt -> {p}")
    try:
        blocks = parse_all()
        ids = [h.get("Id") for h, _ in blocks[:8]]
        print(f"parsed {len(blocks)} AB blocks; first ids: {ids}")
    except Exception as e:
        print(f"parse skipped: {e}")
