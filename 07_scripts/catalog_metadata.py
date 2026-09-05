"""SP08: write FAMILY.yaml per family and project.json per version.

Two facts have to survive the restructure, and neither can be read off a directory name
once SP09 shortens it:

* the **official long name**, because outputs are still called
  `SST_Quantum_Galileo_Action_Gauge_Closure_Falsifier_v0.1.1-outputs/` and that name
  must keep coming from metadata, not from the folder it ran in;
* the **pre-migration path**, so any path in a paper, zip or lab notebook still resolves
  to a family.

Version identifiers are parsed, not rewritten. A four-part `v0.2.2.8` is recorded as
version `v0.2.2` with revision 8; a config-carrying `v0.4.8_Adaptive_Spectral_DD32_compact`
as version `v0.4.8` with config `adaptive-spectral-dd32-compact`. The directory keeps its
name until SP09.

Run with --apply to write; default is a dry run.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WB = Path(__file__).resolve().parents[1]
CATALOG = WB / ".cursor" / "plans" / "restructure" / "CATALOG_v0.1.md"
PATH_MAP = WB / "10_docs" / "migration" / "path_map.csv"

FAMILY_HOMES: dict[str, list[str]] = {
    "01_research": ["A_falsifiers", "B_closures", "C_dynamics",
                    "D_benchmarks", "E_pipelines", "F_exploratory"],
    "02_libraries": ["A_knot_libraries", "B_finite_core", "D_numerics"],
    "04_tools": ["A_geometry", "B_crawlers", "C_fabrication", "D_compute", "D_proof"],
    "05_apps": [""],
}

#: directories inside a family that are not versions
NON_VERSION = {"_variants", "keys", "references", "__pycache__",
               ".venv", ".pytest_cache", "build", "dist"}

KIND_BY_LETTER = {
    "A_falsifiers": "falsifier",
    "B_closures": "closure",
    "C_dynamics": "dynamics",
    "D_benchmarks": "benchmark",
    "E_pipelines": "pipeline",
    "F_exploratory": "exploratory",
    "A_knot_libraries": "library",
    "B_finite_core": "library",
    "D_numerics": "library",
    "A_geometry": "tool",
    "B_crawlers": "tool",
    "C_fabrication": "tool",
    "D_compute": "tool",
    "D_proof": "tool",
    "": "app",
}

FAMILY_DIR = re.compile(r"^([A-F]\d{3})_(.+)$")
CATALOG_ROW = re.compile(r"^\|\s*\*{0,2}([A-F]\d{3})\*{0,2}\s*\|\s*`([^`]+)`\s*\|\s*([^|]+)\|")

#: v1.2.3, v1.2.3.4, v10B1, v0_6, v1.2.3-alpha.1
VERSION_TOKEN = re.compile(
    r"[_-]?v(\d+(?:[._]\d+)*(?:[A-Za-z]\d*)?(?:-[A-Za-z0-9.]+)?)", re.I
)


#: Blinding state is not a configuration. The restructure invariant is that blind and
#: revealed artifacts are never merged, so this gets its own field rather than being
#: flattened into `config` where a later tool might treat it as interchangeable.
BLIND_STATES = {
    "blind_source": "blind",
    "blind": "blind",
    "reveal_key": "reveal_key",
    "unblind_key": "reveal_key",
    "revealed": "revealed",
}


@dataclass
class Version:
    directory: str
    version: str
    revision: int | None = None
    config: str | None = None
    blind: str | None = None


@dataclass
class Family:
    catalog_id: str
    slug: str
    domain: str
    letter: str
    path: Path
    name: str = ""
    versions: list[Version] = field(default_factory=list)
    variants: list[str] = field(default_factory=list)
    legacy_paths: list[str] = field(default_factory=list)
    output_prefix: str = ""
    #: True when no subdirectory carries a version token. Such a family is laid out by
    #: topic (audits/, code/, figures/) or holds distinct unversioned packages. Those
    #: folders must never be recorded as versions: SP09 renames version directories,
    #: and renaming `code/` to a version id would be destructive.
    unversioned: bool = False
    layout: list[str] = field(default_factory=list)
    #: True when the version directories share no common stem, so no single output name
    #: can be derived. F002 holds two genuinely different packages that the catalog
    #: counts as two versions; D002's version-looking folders are demo output. SP09 must
    #: not invent an output_prefix for these - it has to be supplied per version.
    heterogeneous: bool = False


def catalog_names() -> dict[str, str]:
    """catalog_id -> official long name, from the catalog tables."""
    out: dict[str, str] = {}
    for line in CATALOG.read_text(encoding="utf-8").splitlines():
        m = CATALOG_ROW.match(line)
        if m:
            cid, _slug, official = m.group(1), m.group(2), m.group(3).strip()
            # first table wins; later domains reuse ids legitimately
            out.setdefault(f"{cid}|{_slug}", official)
    return out


def legacy_by_id() -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    if not PATH_MAP.is_file():
        return out
    for row in csv.DictReader(PATH_MAP.open(encoding="utf-8-sig")):
        cid = (row.get("catalog_id") or "").strip()
        old = (row.get("old_path") or "").strip()
        if cid and old and "*" not in old:
            out[cid].append(old)
    return {k: sorted(set(v)) for k, v in out.items()}


def parse_version(dirname: str) -> Version:
    """Split a version directory name into version, revision and config."""
    matches = list(VERSION_TOKEN.finditer(dirname))
    if not matches:
        return Version(directory=dirname, version=dirname)

    m = matches[-1]
    raw = m.group(1)
    tail = dirname[m.end():].strip("_-")

    parts = raw.replace("_", ".").split(".")
    revision: int | None = None
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        revision = int(parts[3])
        raw = ".".join(parts[:3])

    config = blind = None
    if tail:
        key = re.sub(r"[\s-]+", "_", tail).lower()
        if key in BLIND_STATES:
            blind = BLIND_STATES[key]
        else:
            config = re.sub(r"[_\s]+", "-", tail).lower()

    return Version(
        directory=dirname, version=f"v{raw}",
        revision=revision, config=config, blind=blind,
    )


def output_prefix_for(versions: list[Version]) -> str:
    """The long official stem that output directories are still named after."""
    stems = []
    for v in versions:
        m = VERSION_TOKEN.search(v.directory)
        if m and m.start() > 0:
            stems.append(v.directory[: m.start()])
    if not stems:
        return ""
    # longest common prefix across version directories
    first = stems[0]
    for s in stems[1:]:
        while not s.startswith(first):
            first = first[:-1]
            if not first:
                return ""
    return first


def sort_key(v: Version) -> tuple:
    nums = re.findall(r"\d+", v.version)
    return tuple(int(n) for n in nums) + (v.revision or 0,)


def discover() -> list[Family]:
    names = catalog_names()
    legacy = legacy_by_id()
    families: list[Family] = []

    for domain, letters in FAMILY_HOMES.items():
        for letter in letters:
            base = WB / domain / letter if letter else WB / domain
            if not base.is_dir():
                continue
            for d in sorted(base.iterdir()):
                if not d.is_dir():
                    continue
                m = FAMILY_DIR.match(d.name)
                if not m:
                    continue
                cid, slug = m.group(1), m.group(2)
                fam = Family(
                    catalog_id=cid, slug=slug, domain=domain, letter=letter, path=d,
                    name=names.get(f"{cid}|{slug}", slug.replace("_", " ").title()),
                    legacy_paths=legacy.get(cid, []),
                )
                children = [
                    c for c in sorted(d.iterdir())
                    if c.is_dir() and c.name not in NON_VERSION
                    and not c.name.startswith(".")
                ]
                versioned = [c for c in children if VERSION_TOKEN.search(c.name)]
                if versioned:
                    fam.versions = [parse_version(c.name) for c in versioned]
                    fam.layout = [c.name for c in children if c not in versioned]
                else:
                    fam.unversioned = True
                    fam.layout = [c.name for c in children]
                variants_dir = d / "_variants"
                if variants_dir.is_dir():
                    fam.variants = sorted(p.name for p in variants_dir.iterdir() if p.is_dir())
                fam.versions.sort(key=sort_key)
                fam.output_prefix = output_prefix_for(fam.versions)
                fam.heterogeneous = bool(fam.versions) and not fam.output_prefix
                families.append(fam)
    return families


def yaml_escape(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def family_yaml(fam: Family) -> str:
    lines = [
        f"catalog_id: {fam.catalog_id}",
        f"domain: {fam.domain}",
    ]
    if fam.letter:
        lines.append(f"letter: {fam.letter}")
    lines += [
        f"slug: {fam.slug}",
        f"name: {yaml_escape(fam.name)}",
        f"kind: {KIND_BY_LETTER.get(fam.letter, 'unknown')}",
        "status: active",
    ]
    if fam.unversioned:
        lines.append("unversioned: true")
    if fam.heterogeneous:
        lines.append("heterogeneous: true")
    if fam.versions:
        lines.append(f"latest: {fam.versions[-1].version}")
    if fam.output_prefix:
        lines.append(f"output_prefix: {yaml_escape(fam.output_prefix)}")

    lines.append("versions:")
    if fam.versions:
        for v in fam.versions:
            lines.append(f"  - id: {v.version}")
            lines.append(f"    directory: {yaml_escape(v.directory)}")
            if v.revision is not None:
                lines.append(f"    revision: {v.revision}")
            if v.config:
                lines.append(f"    config: {yaml_escape(v.config)}")
            if v.blind:
                lines.append(f"    blind: {v.blind}")
    else:
        lines[-1] = "versions: []"

    lines.append("variants:")
    if fam.variants:
        for name in fam.variants:
            lines.append(f"  - {yaml_escape(name)}")
    else:
        lines[-1] = "variants: []"

    lines.append("layout:")
    if fam.layout:
        for name in fam.layout:
            lines.append(f"  - {yaml_escape(name)}")
    else:
        lines[-1] = "layout: []"

    lines.append("legacy_paths:")
    if fam.legacy_paths:
        for p in fam.legacy_paths:
            lines.append(f"  - {yaml_escape(p)}")
    else:
        lines[-1] = "legacy_paths: []"

    return "\n".join(lines) + "\n"


def project_json(fam: Family, v: Version) -> str:
    payload = {
        "catalog_id": fam.catalog_id,
        "name": fam.name,
        "version": v.version,
        "revision": v.revision,
        "config": v.config,
        "blind": v.blind,
        "legacy_dir": v.directory,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    families = discover()
    versions = sum(len(f.versions) for f in families)
    with_rev = sum(1 for f in families for v in f.versions if v.revision is not None)
    with_cfg = sum(1 for f in families for v in f.versions if v.config)
    no_prefix = [f.catalog_id for f in families if not f.output_prefix and f.versions]

    print(f"families            : {len(families)}")
    print(f"version directories : {versions}")
    print(f"  with revision     : {with_rev}")
    print(f"  with config       : {with_cfg}")
    print(f"families lacking an output_prefix: {len(no_prefix)}")
    if no_prefix:
        print("   " + ", ".join(no_prefix[:20]))

    if not args.apply:
        sample = next((f for f in families if f.catalog_id == "A042"), families[0])
        print(f"\n=== sample FAMILY.yaml ({sample.catalog_id}) ===")
        print(family_yaml(sample))
        print("(dry run)")
        return 0

    for fam in families:
        (fam.path / "FAMILY.yaml").write_text(family_yaml(fam), encoding="utf-8")
        for v in fam.versions:
            (fam.path / v.directory / "project.json").write_text(
                project_json(fam, v), encoding="utf-8"
            )
    print(f"\nwrote {len(families)} FAMILY.yaml and {versions} project.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
