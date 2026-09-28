from __future__ import annotations
from pathlib import Path
import hashlib
import json
import re
import zipfile

OUTPUT_RE = re.compile(r"E010_PKLSA_Production_Knot_Link_Basis_v(\d+)\.(\d+)\.(\d+)-outputs$")


def normalize_workbench_root(value: str | Path) -> Path:
    p = Path(value).absolute()
    probes = [p, p / "SST-Workbench", *p.parents]
    seen: set[str] = set()
    for q in probes:
        key = str(q).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            if q.name.lower() == "sst-workbench" and (q / "01_research").is_dir():
                return q
        except OSError:
            continue
    raise RuntimeError(f"could not resolve SST-Workbench root from: {p}")


def _version_key(path: Path) -> tuple[int, int, int]:
    m = OUTPUT_RE.match(path.name)
    return tuple(map(int, m.groups())) if m else (-1, -1, -1)


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def locate_e010_output(workbench_root: str | Path, explicit: str | Path | None = None) -> Path:
    if explicit:
        p = Path(explicit).absolute()
        if p.is_file() and p.suffix.lower() == ".zip":
            return p
        if not (p / "RELEASE.json").is_file():
            raise RuntimeError(f"explicit E010 output has no RELEASE.json: {p}")
        return p

    root = normalize_workbench_root(workbench_root)
    family = root / "01_research" / "E_pipelines" / "E010_pklsa_parametric_knot_link_seed_atlas"
    if not family.is_dir():
        raise RuntimeError(f"E010 family directory not found: {family}")

    candidates: list[Path] = []
    for p in family.rglob("E010_PKLSA_Production_Knot_Link_Basis_v*-outputs"):
        if p.is_dir() and (p / "RELEASE.json").is_file() and OUTPUT_RE.match(p.name):
            candidates.append(p)
    if not candidates:
        raise RuntimeError(f"no E010 production output with RELEASE.json found under: {family}")
    candidates.sort(key=_version_key, reverse=True)
    return candidates[0]


def _zip_root(zf: zipfile.ZipFile) -> str:
    hits = [n for n in zf.namelist() if n.endswith("/RELEASE.json") and n.count("/") == 1]
    if len(hits) != 1:
        raise RuntimeError(f"expected exactly one top-level RELEASE.json in E010 ZIP; found {len(hits)}")
    return hits[0].rsplit("/", 1)[0]


def extract_e010_subset(zip_path: str | Path, topology_ids: list[str], destination: str | Path) -> tuple[Path, dict]:
    """Extract only root ledgers plus requested topology qualification artifacts from an E010 ZIP."""
    zp = Path(zip_path).absolute()
    dest = Path(destination).absolute()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zp) as zf:
        root_name = _zip_root(zf)
        wanted = {
            f"{root_name}/RELEASE.json",
            f"{root_name}/CAMPAIGN_INDEX.json",
            f"{root_name}/FAILED_TOPOLOGIES.json",
            f"{root_name}/RUN_CONTEXT.json",
        }
        qualification_prefixes = [f"{root_name}/atlas/{t}/qualification/" for t in topology_ids]
        metadata_prefixes = []
        for t in topology_ids:
            metadata_prefixes.extend([f"{root_name}/atlas/{t}/sources/", f"{root_name}/atlas/{t}/generated/"])
        for name in zf.namelist():
            is_qualification = any(name.startswith(p) and not name.endswith("/") for p in qualification_prefixes)
            is_carrier_metadata = any(name.startswith(p) and name.endswith(".json") and "/CAR_" in name for p in metadata_prefixes)
            if name in wanted or is_qualification or is_carrier_metadata:
                zf.extract(name, dest)
    out = dest / root_name
    if not (out / "RELEASE.json").is_file():
        raise RuntimeError("subset extraction did not produce RELEASE.json")
    return out, {
        "input_kind": "zip",
        "input_path": str(zp),
        "input_sha256": sha256_file(zp),
        "extracted_topology_count": len(topology_ids),
    }


def validate_e010_release(output_root: str | Path, contract: dict) -> dict:
    root = Path(output_root)
    release = json.loads((root / "RELEASE.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    warnings: list[str] = []

    for key in contract.get("required_release_true", []):
        if release.get(key) is not True:
            errors.append(f"{key} must be true")

    allowed_versions = {str(x) for x in contract.get("allowed_release_versions", [])}
    version = str(release.get("e010_version", ""))
    if allowed_versions and version not in allowed_versions:
        errors.append(f"unsupported e010_version={version!r}; allowed={sorted(allowed_versions)}")

    expected_count = contract.get("expected_topology_count")
    if expected_count is not None and release.get("topology_count") != expected_count:
        errors.append(f"topology_count={release.get('topology_count')!r}; expected {expected_count}")

    if not (root / "CAMPAIGN_INDEX.json").is_file():
        errors.append("CAMPAIGN_INDEX.json missing")

    for key in contract.get("global_campaign_fields_are_advisory", []):
        value = release.get(key)
        if key in {"full_campaign_gate_pass", "publication_ready_geometry_layer"} and value is not True:
            warnings.append(f"{key}={value!r}; E011 will enforce per-topology admission")
        if key == "failed_topology_count" and int(value or 0) > 0:
            warnings.append(f"failed_topology_count={value}; excluded E010 topologies will not enter E011 analysis")

    if errors:
        raise RuntimeError("E010 parent structural gate failed: " + "; ".join(errors))
    return {"release": release, "warnings": warnings}
