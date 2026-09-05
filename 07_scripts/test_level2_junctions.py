"""SP09: ``legacy_dir`` resolves through the two-level junction scaffold."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

WB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WB / "07_scripts"))

import catalog_metadata as cm  # noqa: E402
import junctions as jn  # noqa: E402
import version_rename as vr  # noqa: E402

pytestmark = pytest.mark.skipif(os.name != "nt", reason="junctions need Windows")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _candidates(fam: cm.Family, legacy_dir: str) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for lp in fam.legacy_paths:
        lp = lp.replace("\\", "/").strip()
        if not lp or lp in vr.NEVER_CONVERT:
            continue
        if "/" in lp:
            parent, child = lp.split("/", 1)
            paths = [WB / parent / child, WB / parent / legacy_dir]
        else:
            paths = [WB / lp / legacy_dir]
            if lp == legacy_dir:
                paths.append(WB / lp)
        for p in paths:
            key = Path(str(p))
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
    return out


def _resolves_to(link: Path, dest: Path) -> bool:
    try:
        if jn.is_junction(link):
            return jn.junction_target(link) == dest.resolve()
        if link.exists():
            return link.resolve() == dest.resolve()
    except OSError:
        return False
    return False


def test_legacy_dir_scaffold_resolves_to_the_renamed_directory():
    missing = []
    for fam in cm.discover():
        if not fam.legacy_paths:
            continue
        if all(
            lp.replace("\\", "/").split("/")[0] in vr.NEVER_CONVERT
            for lp in fam.legacy_paths
        ):
            continue
        for v in fam.versions:
            dest = fam.path / v.directory
            pj = dest / "project.json"
            if not pj.is_file():
                continue
            legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            if not legacy:
                continue
            hits = [p for p in _candidates(fam, legacy) if _resolves_to(p, dest)]
            if not hits:
                missing.append((fam.catalog_id, v.directory, legacy))
    assert missing == [], f"legacy_dir does not resolve: {missing[:15]}"


def test_project_json_hash_matches_through_the_scaffold():
    mismatches = []
    for fam in cm.discover():
        if not fam.legacy_paths:
            continue
        if all(
            lp.replace("\\", "/").split("/")[0] in vr.NEVER_CONVERT
            for lp in fam.legacy_paths
        ):
            continue
        for v in fam.versions:
            dest = fam.path / v.directory
            pj = dest / "project.json"
            if not pj.is_file():
                continue
            want = _sha256(pj)
            legacy = (json.loads(pj.read_text(encoding="utf-8")).get("legacy_dir") or "").strip()
            hits = [p for p in _candidates(fam, legacy) if _resolves_to(p, dest)]
            if not hits:
                continue
            via = hits[0] / "project.json"
            if not via.is_file():
                mismatches.append((fam.catalog_id, v.directory, "no project.json via scaffold"))
                continue
            got = _sha256(via)
            if got != want:
                mismatches.append((fam.catalog_id, v.directory, want, got))
    assert mismatches == [], mismatches[:10]
