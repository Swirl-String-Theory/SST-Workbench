from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import re
import sys
import numpy as np

from .utils import sha256_file, geometry_sha256

E010_REL = Path("01_research/E_pipelines/E010_pklsa_parametric_knot_link_seed_atlas")
EXPECTED_CROSS_SCHEMA = "E013-COMMON-CARRIER-MANIFEST-1"
EXPECTED_SKLSA_RELEASE = "E011-v0.3.0"


def locate_e010(workbench: Path):
    from .admission import read, verify_loader, workspace_path
    root = Path(__file__).resolve().parents[1]
    pins = read(root/'admission/RUNTIME_PINS.json')
    return verify_loader(workbench,pins), workspace_path(workbench,pins['e010_production'])


def _import_loader(e010: Path):
    s = str(e010)
    if s not in sys.path:
        sys.path.insert(0, s)
    from pklsa_builder.io_geometry import load_geometry
    try:
        from pklsa_builder.gilbert import find_gilbert_record, sample_gilbert_components
    except Exception:
        find_gilbert_record = sample_gilbert_components = None
    return load_geometry, find_gilbert_record, sample_gilbert_components


def _remap_source(path_str: str | None, workbench: Path):
    if not path_str:
        return None
    p = Path(path_str)
    if p.exists():
        return p
    s = str(path_str).replace("\\", "/")
    marker = "SST-Workbench/"
    if marker in s:
        return workbench / Path(s.split(marker, 1)[1])
    return workbench / p if not p.is_absolute() else p


def load_cross_manifest(path: str | Path) -> dict:
    from .admission import read, validate_manifest
    root = Path(__file__).resolve().parents[1]
    return validate_manifest(path, root.parents[3], read(root/'admission/RUNTIME_PINS.json'))['manifest']


def _load_manifest_geometry(row: dict, e010: Path, workbench: Path):
    loc = row["source_locator"]
    sp = _remap_source(loc.get("source_path"), workbench)
    if sp is None or not sp.is_file():
        raise FileNotFoundError(str(sp))
    raw_expected = loc.get("raw_sha256")
    if raw_expected:
        actual = sha256_file(sp)
        if actual != raw_expected:
            raise ValueError(
                f"raw_sha256 mismatch for {row.get('static_seed_id')}: "
                f"expected={raw_expected} actual={actual}"
            )
    load_geometry, find_gilbert_record, sample_gilbert_components = _import_loader(e010)
    rep = loc.get("representation")
    if rep == "gilbert_ab_record":
        if find_gilbert_record is None:
            raise RuntimeError("Gilbert loader unavailable in E010")
        rec = find_gilbert_record(sp, row["topology_id"])
        n = max(4096, int(row.get("finest_resolution") or 4096))
        comps = sample_gilbert_components(rec, n=n)
    else:
        comps = load_geometry(sp, representation=rep)
    comps = [np.asarray(c, dtype=float) for c in comps]
    actual_geometry = geometry_sha256(comps)
    expected_geometry = row.get("geometry_sha256") or loc.get("geometry_sha256")
    if expected_geometry and actual_geometry != expected_geometry:
        raise ValueError(
            f"geometry_sha256 mismatch for {row.get('static_seed_id')}: "
            f"expected={expected_geometry} actual={actual_geometry}"
        )
    return comps, sp, actual_geometry


def _find_topology_dir(e010_output: Path, topology_id: str) -> Path | None:
    for base in (e010_output / "atlas", e010_output / "poc" / "atlas"):
        p = base / topology_id
        if p.is_dir():
            return p
    return None


def topology_features(topology_dir: Path | None):
    """Best-effort E010 topology-reference scalars; never synthesized from names."""
    if topology_dir is None:
        return {"values": {}, "provenance": {}}
    td = Path(topology_dir) / "topology"
    found, provenance = {}, {}
    wanted = {
        "hyperbolic_volume": ("hyperbolic_volume", "hyperbolic volume", "volume_hyperbolic"),
        "genus": ("genus", "seifert_genus"),
        "bridge_index": ("bridge_index", "bridge number", "bridge_number"),
        "braid_index": ("braid_index", "braid index"),
        "crossing_number": ("crossing_number", "crossing number"),
    }

    def walk(obj, path=()):
        if isinstance(obj, dict):
            for k, v in obj.items():
                kp = " ".join(str(k).lower().replace("-", "_").split())
                for dest, names in wanted.items():
                    if dest in found:
                        continue
                    path_context = " ".join(path).lower()
                    match = kp in names or (
                        dest == "hyperbolic_volume"
                        and (
                            ("hyperbol" in kp and "vol" in kp)
                            or (kp == "volume" and "hyperbol" in path_context)
                        )
                    )
                    if match and isinstance(v, (int, float)) and np.isfinite(v) and float(v) > 0:
                        found[dest] = float(v)
                        provenance[dest] = "/".join(path + (str(k),))
                walk(v, path + (str(k),))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, path + (str(i),))

    if td.is_dir():
        for fp in sorted(td.rglob("*.json")):
            try:
                walk(json.loads(fp.read_text(encoding="utf-8")), (fp.name,))
            except Exception:
                continue
    return {"values": found, "provenance": provenance}


def _manifest_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_carriers(workbench, config):
    """Load only carriers frozen by E013.

    A054-v0.6.0 intentionally has no automatic direct-E010 discovery route.  E010 is
    consulted only to reload the exact source bytes and optional topology metadata
    for carrier IDs already frozen by E013/E011.
    """
    workbench = Path(workbench)
    manifest_env = os.environ.get("SST_CROSS_CARRIER_MANIFEST")
    require = bool(config.get("require_e013_manifest", True))
    fallback = bool(config.get("allow_direct_e010_fallback", False))

    if not manifest_env:
        if require or not fallback:
            raise RuntimeError(
                "A054-v0.6.0 requires SST_CROSS_CARRIER_MANIFEST from E013; "
                "legacy/direct E010 carrier discovery is disabled."
            )
        raise RuntimeError("direct E010 fallback is intentionally not implemented in A054-v0.6.0")

    manifest_path = Path(manifest_env).resolve()
    manifest = load_cross_manifest(manifest_path)
    e010, e010_output = locate_e010(workbench)
    release = json.loads((e010_output / "RELEASE.json").read_text(encoding="utf-8"))

    entries = []
    for row in manifest["carriers"]:
        top = row["topology_id"]
        loc = row["source_locator"]
        carrier = {
            "carrier_id": row["carrier_id"],
            "static_seed_id": row["static_seed_id"],
            "topology_id": top,
            "provider_group": row.get("provider_group"),
            "independence_group": row.get("provider_group"),
            "lineage_group": row.get("lineage_group"),
            "source_family": loc.get("source_family"),
            "source_path": loc.get("source_path"),
            "representation": loc.get("representation"),
            "raw_sha256": loc.get("raw_sha256"),
            "geometry_sha256": row.get("geometry_sha256"),
            "evidence_class": row.get("evidence_class"),
            "e011_static_status": row.get("e011_static_status"),
            "capabilities": row.get("capabilities"),
        }
        rec = {
            "topology_id": top,
            "topology_dir": str(_find_topology_dir(e010_output, top) or ""),
            "topology_features": topology_features(_find_topology_dir(e010_output, top)),
            "carrier": carrier,
            "qualification": {
                "authority": "E013 common carrier manifest / E011 STATIC_READY",
                "static_seed_id": row["static_seed_id"],
                "e011_static_status": row.get("e011_static_status"),
                "evidence_class": row.get("evidence_class"),
            },
            "geometry_sha256": row.get("geometry_sha256"),
            "independence": {
                "evidence_independence_class": row.get("evidence_class"),
                "provider_group": row.get("provider_group"),
                "lineage_group": row.get("lineage_group"),
            },
        }
        try:
            comps, sp, gh = _load_manifest_geometry(row, e010, workbench)
            rec.update({
                "ok": True,
                "components": comps,
                "resolved_source_path": str(sp),
                "verified_geometry_sha256": gh,
            })
        except Exception as ex:
            rec.update({"ok": False, "error": f"{type(ex).__name__}: {ex}"})
        entries.append(rec)

    return {
        "selection_authority": "E013_COMMON_SKLSA_PROVIDER_ANCHORS",
        "manifest_path": str(manifest_path),
        "manifest_sha256": _manifest_digest(manifest_path),
        "campaign_id": os.environ.get("SST_CROSS_CAMPAIGN_ID"),
        "sklsa_release_id": manifest.get("sklsa_release_id"),
        "topology_availability": manifest.get("topology_availability", []),
        "e010": str(e010),
        "output": str(e010_output),
        "release": release,
        "entries": entries,
    }
