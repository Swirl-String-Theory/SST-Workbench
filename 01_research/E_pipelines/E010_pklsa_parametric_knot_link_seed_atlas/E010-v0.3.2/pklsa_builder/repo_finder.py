from __future__ import annotations

"""Repository-wide SST knot-source discovery and coverage auditing.

This module intentionally separates three questions:

1. Where are the source roots now (legacy layout, restructured layout, or moved copies)?
2. What files/artifacts exist under each source root?
3. Which of those artifacts are geometry candidates, topology/reference artifacts,
   metadata, diagnostics, quarantine, or currently unsupported formats?

The finder never promotes a file into a qualified geometry merely because its name
looks like a knot. Geometry admission remains downstream in ``source_discovery`` and
``campaign``.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from collections import Counter
import csv
import fnmatch
import hashlib
import json
import os
import re
from typing import Iterable


DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "data" / "SST_WORKBENCH_KNOT_SOURCES_LOCATIONS_0.1.json"

# Directories which are almost never source data and can make a repository walk explode.
_SKIP_DIRS = {
    ".git", ".svn", ".hg", ".idea", ".vscode", ".venv", "venv", "env",
    "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "build", "dist", "site-packages", "__pypackages__",
}

# We do NOT skip directories merely because they contain "output": KAtlas source crawls
# and historical relaxation campaigns legitimately live in *_Outputs directories.

_GEOMETRY_EXTS = {
    ".xyz", ".vect", ".fseries", ".short", ".locd", ".locf", ".qhp",
    ".kp", ".knot", ".npz", ".npy",
}
_TEXTISH_EXTS = {".txt", ".csv", ".dat"}
_REFERENCE_EXTS = {".json", ".jsonl", ".csv", ".txt", ".md", ".xls", ".xlsx", ".gz", ".zip"}
_DIAGNOSTIC_SUFFIXES = (".struts.vect", ".dlen.vect", ".dvdt.vect", ".log", ".out", ".err")

# Directory aliases are intentionally specific. Generic names such as "knots" only
# participate when their parent path also carries a discriminating token.
_ALIAS_HINTS = {
    "A001": ["knotplot/knots", "a001_knotplot_relaxed", "knotplot_relaxed"],
    "A002": ["knotplot/knots_fourierseries", "a002_knotplot_fourier_series", "knotplot_fourier_series"],
    "A003": ["knotplot/qhp", "qhp_6p3", "qhp_extended", "a003_knotplot_qhp", "knotplot_qhp"],
    "A004": ["ideal_sources", "a004_ideal_gilbert", "ideal_gilbert"],
    "A005": ["katlas_sources_v0.2.2_outputs", "a005_katlas_sources", "katlas_sources"],
    "A006": ["fremlin_fourierseries", "ideal_fremlin_fseries", "a006_fremlin_fourier_series", "fremlin_fourier_series"],
    "A007": ["knot_library", "a007_knot_library_sources", "knot_library_sources"],
    "A008": ["ptsa_parametric_trefoil_seed_atlas_v1.0.0", "a008_parametric_trefoil_seed_atlas", "parametric_trefoil_seed_atlas"],
}

_EXTRA_SOURCE_PATTERNS = {
    "KNOTINFO": ("knotinfo", "3d-coordinates", "pd_3-16"),
    "LINKINFO": ("linkinfo",),
    "RIDGERUNNER": ("ridgerunner", "ridgerunner_cantarella_rawdon"),
    "KATLAS": ("katlas", "knot_atlas"),
    "FREMLIN": ("fremlin",),
    "KNOTPLOT": ("knotplot",),
    "PTSA": ("ptsa", "parametric_trefoil"),
    "QHP": ("qhp",),
}


def _norm(s: str) -> str:
    s = s.replace("\\", "/").lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _path_norm(p: Path | str) -> str:
    return str(p).replace("\\", "/").lower().strip("/")


def load_catalog(path: str | Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_CATALOG
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data.get("sources"), list):
        raise ValueError(f"invalid source catalog: {p}")
    ids = [x.get("catalog_id") for x in data["sources"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate catalog_id in source catalog")
    return data


def _iter_dirs(root: Path, max_depth: int = 7) -> Iterable[Path]:
    root = root.resolve()
    base_parts = len(root.parts)
    for cur, dirs, _files in os.walk(root):
        cp = Path(cur)
        depth = len(cp.parts) - base_parts
        dirs[:] = [d for d in dirs if d.lower() not in _SKIP_DIRS and not d.startswith(".")]
        if depth >= max_depth:
            dirs[:] = []
        yield cp


def _expand_relative_pattern(root: Path, pattern: str) -> list[Path]:
    pattern = pattern.replace("\\", "/").strip("/")
    if "*" in pattern or "?" in pattern or "[" in pattern:
        return [p for p in root.glob(pattern) if p.exists()]
    p = root / pattern
    return [p] if p.exists() else []


def _candidate_path_score(path: Path, root: Path, catalog_id: str, slug: str) -> int:
    try:
        rel = _path_norm(path.relative_to(root))
    except Exception:
        rel = _path_norm(path)
    reln = _norm(rel)
    score = 0
    for hint in _ALIAS_HINTS.get(catalog_id, []):
        hn = _norm(hint)
        if hn == reln:
            score = max(score, 100)
        elif hn in reln:
            score = max(score, 80)
    slugn = _norm(slug)
    if slugn and slugn in reln:
        score = max(score, 70)
    if catalog_id.lower() in rel.lower():
        score = max(score, 65)
    # Special structural matches for paths whose final directory is too generic alone.
    if catalog_id == "A001" and "knotplot" in rel and re.search(r"(^|/)knots($|/)", rel):
        score = max(score, 95)
    if catalog_id == "A002" and "knotplot" in rel and "fourier" in rel:
        score = max(score, 95)
    if catalog_id == "A003" and "qhp" in rel:
        score = max(score, 95)
    return score


def resolve_source_roots(repo_root: str | Path, catalog: dict, search_depth: int = 7) -> dict[str, list[dict]]:
    root = Path(repo_root).resolve()
    if not root.exists():
        raise FileNotFoundError(root)
    resolved: dict[str, list[dict]] = {}
    dirs_cache = None
    for src in catalog["sources"]:
        cid = src["catalog_id"]
        hits: dict[str, dict] = {}
        # 1. Explicit authoritative legacy paths.
        for lp in src.get("legacy_paths", []):
            for p in _expand_relative_pattern(root, lp):
                if p.is_dir():
                    hits[str(p.resolve())] = {"path": str(p.resolve()), "resolution": "legacy_exact", "score": 100}
        # 2. Post-restructure destination.
        dest = src.get("destination")
        if dest:
            for p in _expand_relative_pattern(root, dest):
                if p.is_dir():
                    hits[str(p.resolve())] = {"path": str(p.resolve()), "resolution": "destination_exact", "score": 100}
        # 3. Repo-wide alias search only when explicit paths are insufficient. This also
        # catches partially completed restructures and moved copies.
        if not hits:
            if dirs_cache is None:
                dirs_cache = list(_iter_dirs(root, max_depth=search_depth))
            scored = []
            for p in dirs_cache:
                s = _candidate_path_score(p, root, cid, src.get("slug", ""))
                if s >= 70:
                    scored.append((s, len(p.parts), p))
            # Keep best distinct roots; when a parent and child both match, prefer the
            # more specific/high-score path and suppress descendants already covered.
            for s, _depth, p in sorted(scored, key=lambda x: (-x[0], x[1], str(x[2]))):
                rp = p.resolve()
                if any(rp == Path(v["path"]) or rp.is_relative_to(Path(v["path"])) for v in hits.values()):
                    continue
                hits[str(rp)] = {"path": str(rp), "resolution": "repo_alias_search", "score": s}
                if len(hits) >= 8:
                    break
        resolved[cid] = list(hits.values())
    return resolved


def _looks_xyz_text(path: Path, max_bytes: int = 8192) -> bool:
    try:
        raw = path.read_bytes()[:max_bytes]
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return False
    good = 0
    for line in text.splitlines()[:80]:
        s = line.strip()
        if not s or s.startswith(("#", "%", "//")):
            continue
        cols = s.replace(",", " ").split()
        if len(cols) < 3:
            continue
        try:
            float(cols[0]); float(cols[1]); float(cols[2])
            good += 1
        except Exception:
            continue
    return good >= 3


def _looks_xyz_triplets(path: Path, max_bytes: int = 8192) -> bool:
    """Detect sampled XYZ text even when the filename has a Fourier-ish suffix.

    A007 contains historical mirrors where some ``.fseries`` files are actually
    three-column sampled centerlines.  Extension-only classification therefore
    corrupts ingestion.  Require a strong majority of numeric data rows to have
    exactly three columns; true Fremlin coefficient rows have six.
    """
    try:
        raw = path.read_bytes()[:max_bytes]
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return False
    numeric_rows = 0
    triplets = 0
    for line in text.splitlines()[:120]:
        t = line.strip()
        if not t or t.startswith(("#", "%", "//")):
            continue
        cols = t.replace(",", " ").split()
        try:
            [float(x) for x in cols]
        except Exception:
            continue
        if len(cols) < 3:
            continue
        numeric_rows += 1
        if len(cols) == 3:
            triplets += 1
    return numeric_rows >= 3 and triplets >= 3 and triplets / numeric_rows >= 0.8



def _is_comment_only_fseries(path: Path, max_bytes: int = 8192) -> bool:
    """Return True only for a header/comment-only ``.fseries`` placeholder.

    This is intentionally narrow. A007 contains historical mirror files whose
    ``.fseries`` payload can be provenance/header comments only while the actual
    sampled geometry is carried by an adjacent ``.short`` file. In the observed
    Fremlin 8_5 mirror this represents an incomplete mirror artifact, not a
    valid zero-harmonic Fourier geometry. The artifact stays in the source
    inventory but must not become a geometry carrier. Any non-comment content returns False so malformed candidate
    geometry continues down the normal fail-closed path.
    """
    if path.suffix.lower() != ".fseries":
        return False
    try:
        raw = path.read_bytes()[:max_bytes]
        text = raw.decode("utf-8", errors="ignore")
    except Exception:
        return False
    saw_comment = False
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith(("#", "%", "//")):
            saw_comment = True
            continue
        return False
    return saw_comment


def _classify_catalog_file(path: Path, catalog_id: str, source_root: Path) -> tuple[str, str]:
    """Return (role, representation_hint)."""
    lname = path.name.lower()
    rel = _path_norm(path.relative_to(source_root))
    suffix = path.suffix.lower()

    if lname.endswith(_DIAGNOSTIC_SUFFIXES):
        return "diagnostic", "diagnostic"
    if any(seg.lower() == "quarantine" for seg in path.parts):
        return "quarantine", "quarantine"
    if any(seg.lower() == "reveal_only" for seg in path.parts):
        return "restricted_metadata", "reveal_only"

    if catalog_id == "A001":
        if lname == "ideal.txt":
            return "geometry", "knotplot_ideal_xyz"
        if suffix in {".locd", ".locf"}:
            return "geometry", "knotplot_binary"
        if suffix == ".vect":
            return "geometry", "vect"
        if suffix in {".xyz", ".npz", ".npy"}:
            return "geometry", suffix.lstrip(".")
        if suffix in _TEXTISH_EXTS and _looks_xyz_text(path):
            return "geometry", "xyz_text"
        return "metadata", suffix.lstrip(".") or "unknown"

    if catalog_id == "A002":
        if suffix == ".fseries":
            return "geometry", "fseries"
        if suffix == ".short" and _looks_xyz_text(path):
            return "geometry", "xyz_short"
        return "metadata", suffix.lstrip(".") or "unknown"

    if catalog_id == "A003":
        if suffix in {".qhp", ".xyz", ".vect", ".locd", ".locf", ".kp", ".knot", ".npz", ".npy"}:
            return "geometry", "qhp" if suffix == ".qhp" else suffix.lstrip(".")
        if suffix in _TEXTISH_EXTS and _looks_xyz_text(path):
            return "geometry", "xyz_text"
        return "metadata", suffix.lstrip(".") or "qhp_unknown"

    if catalog_id == "A004":
        if lname.startswith("ideal") and lname.endswith(".txt.gz"):
            return "geometry_catalog", "gilbert_ab_catalog"
        if lname in {"knots_ideal_favorites.txt", "rhof_triage.csv"}:
            return "selection_metadata", suffix.lstrip(".")
        return "metadata", suffix.lstrip(".") or "unknown"

    if catalog_id == "A005":
        if suffix in {".xyz", ".vect", ".npz"}:
            return "derived_geometry", suffix.lstrip(".")
        return "topology_reference", suffix.lstrip(".") or "unknown"

    if catalog_id == "A006":
        if suffix == ".fseries":
            return "geometry", "fremlin_fseries"
        if suffix == ".short" and _looks_xyz_text(path):
            return "geometry", "xyz_short"
        return "metadata", suffix.lstrip(".") or "unknown"

    if catalog_id == "A007":
        parts = [x.lower() for x in path.parts]
        if "quarantine" in parts:
            return "quarantine", suffix.lstrip(".") or "unknown"
        if "registry" in parts:
            return "registry", suffix.lstrip(".") or "unknown"
        if "derived" in parts:
            # Fremlin/KnotPlot .short files are sampled XYZ point sets when they
            # contain at least three numeric columns.  Do not treat them as
            # Fourier-coefficient files merely because they live in a Fremlin tree.
            if suffix == ".short" and _looks_xyz_triplets(path):
                return "derived_geometry", "xyz_short"
            if suffix == ".fseries" and _looks_xyz_triplets(path):
                return "derived_geometry", "xyz_text"
            if suffix == ".fseries" and _is_comment_only_fseries(path):
                return "derived_metadata", "fseries_header_only_incomplete_mirror"
            if suffix == ".short":
                return "derived_metadata", "short"
            if suffix in _GEOMETRY_EXTS or (suffix in _TEXTISH_EXTS and _looks_xyz_text(path)):
                return "derived_geometry", suffix.lstrip(".") or "xyz_text"
            return "derived_metadata", suffix.lstrip(".") or "unknown"
        if "sources" in parts:
            if suffix == ".short" and _looks_xyz_triplets(path):
                return "source_geometry", "xyz_short"
            if suffix == ".fseries" and _looks_xyz_triplets(path):
                return "source_geometry", "xyz_text"
            if suffix == ".fseries" and _is_comment_only_fseries(path):
                return "source_metadata", "fseries_header_only_incomplete_mirror"
            if suffix == ".short":
                return "source_metadata", "short"
            if suffix in _GEOMETRY_EXTS or (suffix in _TEXTISH_EXTS and _looks_xyz_text(path)):
                return "source_geometry", suffix.lstrip(".") or "xyz_text"
            return "source_metadata", suffix.lstrip(".") or "unknown"
        return "container_metadata", suffix.lstrip(".") or "unknown"

    if catalog_id == "A008":
        if "candidates/" in rel or "/candidates/" in f"/{rel}":
            if suffix == ".xyz":
                return "generated_geometry", "xyz"
        if "controls/" in rel or "/controls/" in f"/{rel}":
            if suffix == ".xyz":
                return "generated_control_geometry", "xyz"
        if suffix == ".xyz" and lname.startswith("ptsa_"):
            return "generated_geometry", "xyz"
        return "metadata", suffix.lstrip(".") or "unknown"

    if suffix in _GEOMETRY_EXTS or (suffix in _TEXTISH_EXTS and _looks_xyz_text(path)):
        return "geometry", suffix.lstrip(".") or "xyz_text"
    return "metadata", suffix.lstrip(".") or "unknown"


def _directory_fingerprint(files: list[dict]) -> str:
    h = hashlib.sha256()
    for r in sorted(files, key=lambda x: x["relative_path"]):
        h.update(r["relative_path"].encode("utf-8", errors="surrogatepass"))
        h.update(b"\0")
        h.update(str(r.get("size", 0)).encode("ascii"))
        h.update(b"\0")
        h.update(str(r.get("mtime_ns", 0)).encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def inventory_source_root(path: str | Path, catalog_id: str, hash_files: bool = False) -> dict:
    root = Path(path).resolve()
    records = []
    errors = []
    if not root.exists():
        return {"root": str(root), "file_count": 0, "errors": ["root_missing"], "files": []}
    for cur, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d.lower() not in _SKIP_DIRS and not d.startswith(".")]
        cp = Path(cur)
        for fn in files:
            p = cp / fn
            try:
                st = p.stat()
                role, rep = _classify_catalog_file(p, catalog_id, root)
                rec = {
                    "path": str(p),
                    "relative_path": p.relative_to(root).as_posix(),
                    "size": st.st_size,
                    "mtime_ns": st.st_mtime_ns,
                    "suffix": p.suffix.lower(),
                    "role": role,
                    "representation_hint": rep,
                }
                anchor_roles={"topology_reference","registry","selection_metadata","source_metadata","derived_metadata","restricted_metadata","quarantine"}
                anchor_names={"source.md","provenance.md","manifest.json","sha256sums.txt","release.json","parameter_grid.json","atlas_public_manifest.json"}
                should_hash = hash_files or (role in anchor_roles and st.st_size <= 32*1024*1024) or (lname := p.name.lower()) in anchor_names
                if should_hash:
                    hh = hashlib.sha256()
                    with p.open("rb") as f:
                        for chunk in iter(lambda: f.read(1024 * 1024), b""):
                            hh.update(chunk)
                    rec["sha256"] = hh.hexdigest()
                    rec["sha256_scope"] = "deep" if hash_files else "reference_anchor"
                records.append(rec)
            except Exception as e:
                errors.append({"path": str(p), "error": f"{type(e).__name__}: {e}"})
    roles = Counter(x["role"] for x in records)
    exts = Counter(x["suffix"] or "<none>" for x in records)
    return {
        "root": str(root),
        "file_count": len(records),
        "byte_count": sum(x["size"] for x in records),
        "roles": dict(sorted(roles.items())),
        "extensions": dict(sorted(exts.items())),
        "quick_fingerprint_sha256": _directory_fingerprint(records),
        "hash_mode": "sha256_each_file" if hash_files else "path_size_mtime_fingerprint",
        "errors": errors,
        "files": records,
    }



def declared_location_checks(repo_root: str | Path, src: dict) -> list[dict]:
    root=Path(repo_root).resolve()
    out=[]
    legacy_map=src.get("legacy_on_disk") or {}
    dest=src.get("destination")
    dest_hits=_expand_relative_pattern(root,dest) if dest else []
    destination_present=any(x.exists() for x in dest_hits)
    for lp in src.get("legacy_paths",[]):
        hits=_expand_relative_pattern(root,lp)
        # legacy_on_disk keys retain trailing slashes in the supplied catalogue.
        expected=legacy_map.get(lp)
        if expected is None:
            expected=legacy_map.get(lp.rstrip("/"))
        if expected is None:
            # For wildcard entries, inspect all matching catalogue keys.
            keys=[k for k in legacy_map if fnmatch.fnmatch(k.rstrip("/"),lp.rstrip("/"))]
            expected=any(bool(legacy_map[k]) for k in keys) if keys else None
        if hits:
            status="PRESENT_LEGACY"
        elif destination_present:
            status="PRESENT_RESTRUCTURED"
        elif expected is False:
            status="ABSENT_EXPECTED_FALSE"
        elif expected is True:
            status="MISSING_EXPECTED_TRUE"
        else:
            status="ABSENT_UNSPECIFIED"
        out.append({"kind":"legacy_path","legacy_path":lp,"expected_on_disk":expected,"status":status,"hits":[str(x.resolve()) for x in hits],"destination_present":destination_present})
    extra_map=src.get("extra_files_on_disk") or {}
    for ef in src.get("extra_files",[]):
        p=root/ef
        expected=extra_map.get(ef)
        if p.exists():
            status="PRESENT_LEGACY"
            hits=[str(p.resolve())]
        elif destination_present:
            # The restructure moves these files under the source destination. Check both
            # destination root and basename explicitly where possible.
            dh=[]
            for d in dest_hits:
                q=d/Path(ef).name
                if q.exists(): dh.append(str(q.resolve()))
            if dh:
                status="PRESENT_RESTRUCTURED"; hits=dh
            elif expected is True:
                status="MISSING_EXPECTED_TRUE"; hits=[]
            else:
                status="ABSENT_UNSPECIFIED"; hits=[]
        elif expected is False:
            status="ABSENT_EXPECTED_FALSE"; hits=[]
        elif expected is True:
            status="MISSING_EXPECTED_TRUE"; hits=[]
        else:
            status="ABSENT_UNSPECIFIED"; hits=[]
        out.append({"kind":"extra_file","legacy_path":ef,"expected_on_disk":expected,"status":status,"hits":hits,"destination_present":destination_present})
    return out

def _expected_on_disk(src: dict) -> bool:
    vals = list((src.get("legacy_on_disk") or {}).values())
    return any(bool(x) for x in vals)


def _source_terminal_status(src: dict, root_inventories: list[dict]) -> tuple[str, str]:
    if not root_inventories:
        if not _expected_on_disk(src):
            return "SOURCE_UNAVAILABLE_WITH_PROVENANCE", "catalog records legacy source as unavailable/moved"
        return "EXPECTED_SOURCE_MISSING", "catalog expected source on disk but repo-wide search found no root"
    total_files = sum(x["file_count"] for x in root_inventories)
    role_counts = Counter()
    for inv in root_inventories:
        role_counts.update(inv.get("roles", {}))
    if total_files == 0:
        return "EMPTY_SOURCE_ROOT", "source root exists but contains no files"
    cid = src["catalog_id"]
    if cid == "A005" and role_counts.get("topology_reference", 0) > 0:
        return "INGESTED", "topology/reference source discovered"
    admissible_roles = {
        "geometry", "geometry_catalog", "source_geometry", "derived_geometry",
        "generated_geometry", "generated_control_geometry",
    }
    if any(role_counts.get(r, 0) > 0 for r in admissible_roles):
        return "INGESTED", "one or more geometry/catalog candidates discovered"
    if cid == "A007" and (role_counts.get("registry", 0) or role_counts.get("source_metadata", 0)):
        return "INGESTED_METADATA_ONLY", "Knot Library provenance/registry found but no geometry candidates in resolved root"
    return "FORMAT_UNSUPPORTED_OR_METADATA_ONLY", "source exists but no geometry/reference artifacts recognized"


def _is_within(path: Path, roots: list[Path]) -> bool:
    rp = path.resolve()
    for r in roots:
        try:
            if rp == r or rp.is_relative_to(r):
                return True
        except Exception:
            pass
    return False


def find_unregistered_source_candidates(repo_root: str | Path, known_roots: list[str], max_depth: int = 6, max_results: int = 500) -> list[dict]:
    root = Path(repo_root).resolve()
    kr = [Path(x).resolve() for x in known_roots]
    results = []
    for p in _iter_dirs(root, max_depth=max_depth):
        if p == root or _is_within(p, kr):
            continue
        rel = _path_norm(p.relative_to(root))
        name = p.name.lower()
        hits = []
        for label, pats in _EXTRA_SOURCE_PATTERNS.items():
            if any(tok in rel for tok in pats):
                hits.append(label)
        if not hits:
            continue
        # Require at least one source-looking file directly in the directory to reduce noise.
        try:
            direct = [x for x in p.iterdir() if x.is_file()]
        except Exception:
            continue
        strong_files = [x for x in direct if x.suffix.lower() in (_GEOMETRY_EXTS | _REFERENCE_EXTS | _TEXTISH_EXTS)]
        if not strong_files:
            continue
        results.append({
            "path": str(p),
            "relative_path": p.relative_to(root).as_posix(),
            "candidate_classes": sorted(hits),
            "direct_file_count": len(direct),
            "source_like_direct_files": [x.name for x in strong_files[:20]],
            "status": "UNREGISTERED_REVIEW_REQUIRED",
        })
        if len(results) >= max_results:
            break
    return results


def scan_repository(repo_root: str | Path, catalog_path: str | Path | None = None, *, hash_files: bool = False, search_depth: int = 7, find_unregistered: bool = True) -> dict:
    root = Path(repo_root).resolve()
    catalog = load_catalog(catalog_path)
    resolved = resolve_source_roots(root, catalog, search_depth=search_depth)
    source_results = []
    all_roots = []
    for src in catalog["sources"]:
        cid = src["catalog_id"]
        roots = resolved.get(cid, [])
        all_roots.extend(x["path"] for x in roots)
        invs = [inventory_source_root(x["path"], cid, hash_files=hash_files) for x in roots]
        # Files catalogued beside a source directory (currently A004 selection/triage files)
        # are preserved as provenance anchors even though they are not centerlines.
        extra_file_records=[]
        for ef in src.get("extra_files",[]):
            candidates=[root/ef]
            dest=src.get("destination")
            if dest:
                candidates.append(root/dest/Path(ef).name)
            for ep in candidates:
                if not ep.exists() or not ep.is_file(): continue
                st=ep.stat(); hh=hashlib.sha256(ep.read_bytes()).hexdigest() if st.st_size <= 32*1024*1024 or hash_files else None
                extra_file_records.append({"path":str(ep.resolve()),"name":ep.name,"size":st.st_size,"sha256":hh,"role":"catalog_extra_file"})
                break
        loc_checks=declared_location_checks(root,src)
        status, reason = _source_terminal_status(src, invs)
        missing_declared=[x for x in loc_checks if x["status"]=="MISSING_EXPECTED_TRUE"]
        if missing_declared:
            status="DECLARED_SUBSOURCE_MISSING"
            reason="one or more catalogue paths expected on disk were not found and no restructured destination was present"
        role_counts = Counter(); ext_counts = Counter()
        for inv in invs:
            role_counts.update(inv.get("roles", {})); ext_counts.update(inv.get("extensions", {}))
        source_results.append({
            "catalog_id": cid,
            "slug": src.get("slug"),
            "description": src.get("description"),
            "expected_on_disk": _expected_on_disk(src),
            "resolved_roots": roots,
            "declared_location_checks": loc_checks,
            "root_inventories": invs,
            "extra_file_records": extra_file_records,
            "status": status,
            "status_reason": reason,
            "file_count": sum(x["file_count"] for x in invs),
            "byte_count": sum(x["byte_count"] for x in invs),
            "role_counts": dict(sorted(role_counts.items())),
            "extension_counts": dict(sorted(ext_counts.items())),
        })
    allowed = {"INGESTED", "INGESTED_METADATA_ONLY", "SOURCE_UNAVAILABLE_WITH_PROVENANCE"}
    blocking = [x for x in source_results if x["status"] not in allowed]
    unregistered = find_unregistered_source_candidates(root, all_roots, max_depth=search_depth) if find_unregistered else []
    return {
        "schema": "PKLSA-REPO-SOURCE-DISCOVERY-2",
        "repo_root": str(root),
        "catalog_schema": catalog.get("schema"),
        "catalog_count": len(catalog.get("sources", [])),
        "source_results": source_results,
        "coverage_gate": {
            "required_catalog_ids": [x["catalog_id"] for x in catalog["sources"]],
            "allowed_terminal_states": sorted(allowed),
            "blocking": [{"catalog_id": x["catalog_id"], "status": x["status"], "reason": x["status_reason"]} for x in blocking],
            "pass": not blocking,
        },
        "unregistered_source_candidates": unregistered,
        "unregistered_review_required": bool(unregistered),
        "hash_mode": "sha256_each_file" if hash_files else "fast_path_size_mtime",
        "guard": "Source discovery is provenance/inventory only. A discovered file is not a qualified geometry until downstream parsing and qualification succeeds.",
    }


def write_scan_outputs(scan: dict, out_dir: str | Path) -> None:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    # Full JSON includes per-file inventories and can be large; gzip it.
    full = out / "REPO_SOURCE_DISCOVERY.json.gz"
    import gzip
    with gzip.open(full, "wt", encoding="utf-8") as f:
        json.dump(scan, f, ensure_ascii=False, sort_keys=True)
    compact = {
        k: v for k, v in scan.items()
        if k not in {"source_results"}
    }
    compact["source_results"] = []
    for s in scan["source_results"]:
        compact["source_results"].append({k: v for k, v in s.items() if k != "root_inventories"})
    (out / "REPO_SOURCE_DISCOVERY_SUMMARY.json").write_text(json.dumps(compact, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    fields = ["catalog_id", "slug", "status", "expected_on_disk", "file_count", "byte_count", "resolved_root_count", "status_reason"]
    with (out / "A001_A008_COVERAGE.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for s in scan["source_results"]:
            w.writerow({
                "catalog_id": s["catalog_id"], "slug": s["slug"], "status": s["status"],
                "expected_on_disk": s["expected_on_disk"], "file_count": s["file_count"], "byte_count": s["byte_count"],
                "resolved_root_count": len(s["resolved_roots"]), "status_reason": s["status_reason"],
            })
    (out / "UNREGISTERED_SOURCE_CANDIDATES.json").write_text(json.dumps(scan["unregistered_source_candidates"], indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def iter_file_records(scan: dict, catalog_id: str | None = None, roles: set[str] | None = None):
    for src in scan.get("source_results", []):
        if catalog_id and src.get("catalog_id") != catalog_id:
            continue
        for inv in src.get("root_inventories", []):
            root = inv.get("root")
            for rec in inv.get("files", []):
                if roles and rec.get("role") not in roles:
                    continue
                x = dict(rec)
                x["catalog_id"] = src.get("catalog_id")
                x["catalog_slug"] = src.get("slug")
                x["source_root"] = root
                yield x
